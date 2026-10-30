# Rótulos do Claude no treino: plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Treinar o modelo clássico com 2.500 rótulos do Claude (mais as regras como variáveis), escolher modelo e limiar num conjunto de desenvolvimento de 500 e avaliar uma vez no ouro, mirando passar dos 60,5% do Qwen nas 53 do Mateus.

**Architecture:** `selecao.py` escolhe uma vez o que rotular; `rotulagem.py` prepara lotes, junta e valida os rótulos que os agentes devolvem; `modelo.py` ganha as regras como variáveis e três modelos candidatos; `desenvolvimento.py` compara candidatos no desenvolvimento, escolhe, calcula o limiar e grava a fila e as predições no ouro. A supervisão fraca continua como referência em `results/supervisao_fraca/`.

**Tech Stack:** Python 3.9+, pandas, numpy, scikit-learn, matplotlib, joblib, pytest. Nada novo.

**Spec:** `docs/superpowers/specs/2026-10-30-rotulos-claude-design.md`

## Global Constraints

- Só ML clássico na triagem: nada de embeddings, transformers ou LLM no código que roda no `make tudo`.
- `make tudo` roda sem Ollama e sem chamar o Claude; os rótulos do Claude ficam em `data/rotulos_claude.csv`, versionado.
- `data/ouro.csv` só é lido em `avaliar.py`. Agentes que rotulam nunca leem `data/ouro.csv`, `rotulagem/` nem `results/`.
- Nenhuma escolha (modelo, forma de treino, hiperparâmetro, limiar) olha o ouro; tudo é escolhido no desenvolvimento.
- Desenvolvimento: 500 sorteadas com `random_state=2026`, excluindo os ids de `dados.amostra_desenvolvimento(200, seed)` para `seed` em 0, 1, 2, 3. Treino: 1.000 sorteadas (`random_state=2026`) e 1.500 de menor certeza, sem sobreposição.
- O modelo final treina só com os 2.500 de treino (mais regras, se a forma B vencer); o desenvolvimento não entra.
- Python 3.9: `from __future__ import annotations`; `SEED_NOVO = 2026` para tudo que é novo.
- Os 53 rótulos com `fonte == mateus` não mudam. Textos do Mateus sem travessões e sem números inventados.
- Trabalhar no branch `rotulos-claude`; sem push sem o Mateus pedir; `/code-review` antes de finalizar.

## Review Focus

1. Agente devolve id faltando, repetido, inventado ou rótulo fora das 7 categorias: `juntar_rotulos` falha com a lista dos ids problemáticos, sem gravar nada. Testes na Task 3.
2. Desenvolvimento contaminado: nenhum id do desenvolvimento está no treino nem nas amostras lidas para escrever as regras. Teste na Task 2.
3. Categoria que nenhum rótulo do treino tem: as probabilidades de qualquer candidato (logística, SVM, NB) ainda trazem as 7 colunas. Teste na Task 4.
4. Forma B com peso: `sample_weight` chega ao classificador nos três candidatos sem erro. Teste na Task 5.
5. Agente que devolve `duvida` como texto ("sim", "true", "1"): é lido como booleano. Teste na Task 3.

---

### Task 1: Guia de rotulagem e supervisão fraca em pasta própria

**Files:**
- Modify: `src/triagem/taxonomia.py` (adicionar `GUIA_ROTULAGEM`)
- Modify: `src/triagem/triagem.py` (saídas em `results/supervisao_fraca/`)
- Modify: `tests/test_triagem.py`, `.gitignore`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Produces: `taxonomia.GUIA_ROTULAGEM: str`; `triagem.PASTA_SUPERVISAO = "supervisao_fraca"`. `triagem.main()` passa a gravar `results/supervisao_fraca/{triagem.csv,modelo.joblib}`; as predições no ouro continuam em `results/preds/ouro__supervisao-fraca__*.jsonl`.

- [ ] **Step 0:** `git switch -c rotulos-claude`
- [ ] **Step 1: Testes que falham**

```python
def test_guia_tem_categorias_e_regra_principal():
    from triagem.taxonomia import GUIA_ROTULAGEM
    assert all(r in GUIA_ROTULAGEM for r in ROTULOS)
    assert "problema que originou" in GUIA_ROTULAGEM
```
Em `test_triagem_csv_sem_ouro`, trocar o caminho lido para `tmp_path / "results" / "supervisao_fraca" / "triagem.csv"`.

- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_pipeline.py tests/test_triagem.py -q` → FAIL (`ImportError` em `GUIA_ROTULAGEM` e arquivo inexistente).
- [ ] **Step 3: Implementar.** `GUIA_ROTULAGEM` = as definições de `CATEGORIAS` em lista, o `REGRAS` e estes parágrafos (texto exato, vindo de `rotulagem/template.html`):

```
- Escolha o problema que originou a reclamação. Consequências (loja não responde, pedi reembolso) só viram o rótulo quando são o único problema citado.
- nao_recebido_atraso vence quando a pessoa ainda não recebeu nada daquele pedido. Se recebeu parte, é item_faltando.
- defeito_qualidade é quando chegou o produto certo, mas quebrado, com defeito ou ruim.
- cobranca_cancelamento é quando o dinheiro é o assunto: cobrança indevida, estorno não feito, cancelamento sem pedido.
- outro cobre elogios com nota baixa, texto sem sentido e o que não couber em nada.
- Se ficar em dúvida entre duas, escolha a melhor e marque dúvida.
```
Em `triagem.main()`, `res_sf = dados.RAIZ / "results" / PASTA_SUPERVISAO`, criar a pasta e gravar ali `triagem.csv` e `modelo.joblib`. Adicionar `results/supervisao_fraca/*.joblib` e `data/lotes/` ao `.gitignore`. Mover o `results/triagem.csv` versionado com `git mv results/triagem.csv results/supervisao_fraca/triagem.csv`.
- [ ] **Step 4:** mesmo comando → PASS. Rodar `PYTHONPATH=src .venv/bin/python -m triagem.triagem` e conferir que `results/supervisao_fraca/modelo.joblib` existe.
- [ ] **Step 5: Commit** — `git add -A src tests .gitignore results/supervisao_fraca && git commit -m "Guarda o guia de rotulagem e move a supervisão fraca para pasta própria"`

---

### Task 2: Seleção do que rotular

**Files:**
- Create: `src/triagem/selecao.py`
- Test: `tests/test_selecao.py`

**Interfaces:**
- Consumes: `dados.pool_de_treino()`, `dados.amostra_desenvolvimento(n, seed)`, `results/supervisao_fraca/modelo.joblib` (`{"modelo": Pipeline, ...}`), `modelo.probabilidades`.
- Produces:
  - `SEED_NOVO = 2026`; `N_DEV, N_ALEATORIO, N_INCERTO = 500, 1000, 1500`.
  - `ids_lidos_para_regras() -> set[str]`: união dos ids de `amostra_desenvolvimento(200, s)` para `s` em 0..3.
  - `selecionar(pool: pd.DataFrame, certeza: pd.Series, excluir_do_dev: set[str]) -> pd.DataFrame` com colunas `review_id, texto, grupo, certeza`; `grupo` em `dev`, `aleatorio`, `incerto`. `certeza` alinhada ao índice de `pool`.
  - CLI `python -m triagem.selecao`: certeza = maior probabilidade do modelo da supervisão fraca no pool; grava `data/para_rotular.csv`. Fica fora do `make tudo`.

- [ ] **Step 1: Testes que falham**

```python
def pool_falso(n=4000):
    return pd.DataFrame({"review_id": [f"r{i}" for i in range(n)], "texto": [f"t{i}" for i in range(n)]})

def test_tamanhos_e_grupos_disjuntos():
    pool = pool_falso(); cert = pd.Series(np.linspace(0, 1, len(pool)))
    s = selecionar(pool, cert, set())
    assert s.grupo.value_counts().to_dict() == {"dev": 500, "aleatorio": 1000, "incerto": 1500}
    assert s.review_id.is_unique

def test_dev_exclui_ids_lidos():
    pool = pool_falso(); cert = pd.Series(0.5, index=pool.index)
    excluir = {f"r{i}" for i in range(0, 4000, 2)}
    s = selecionar(pool, cert, excluir)
    assert not set(s[s.grupo == "dev"].review_id) & excluir

def test_incerto_tem_menor_certeza_do_restante():
    pool = pool_falso(); cert = pd.Series(np.linspace(0, 1, len(pool)))
    s = selecionar(pool, cert, set())
    resto = pool[~pool.review_id.isin(s[s.grupo != "incerto"].review_id)]
    limite = cert[resto.index].sort_values().iloc[1499]
    assert (s[s.grupo == "incerto"].certeza <= limite).all()

def test_reproduzivel():
    pool = pool_falso(); cert = pd.Series(np.linspace(0, 1, len(pool)))
    assert selecionar(pool, cert, set()).equals(selecionar(pool, cert, set()))

def test_ids_lidos_para_regras_fora_do_ouro():
    ids = ids_lidos_para_regras()
    assert 600 <= len(ids) <= 800
    assert not ids & set(dados.amostra_ouro(dados.reclamacoes()).review_id)
```
- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_selecao.py -q` → FAIL (`ModuleNotFoundError`).
- [ ] **Step 3: Implementar.** Ordem: dev = `pool[~excluir].sample(500, random_state=2026)`; do restante, aleatório = `sample(1000, random_state=2026)`; do que sobra, incerto = 1.500 menores `certeza` (empate por `review_id`).
- [ ] **Step 4:** mesmo comando → PASS. Rodar `PYTHONPATH=src .venv/bin/python -m triagem.selecao` → `data/para_rotular.csv` com 3.000 linhas.
- [ ] **Step 5: Commit** — `git add src/triagem/selecao.py tests/test_selecao.py data/para_rotular.csv && git commit -m "Seleciona as mensagens para o Claude rotular"`

---

### Task 3: Lotes, junção e checagem dos rótulos

**Files:**
- Create: `src/triagem/rotulagem.py`
- Test: `tests/test_rotulagem.py`

**Interfaces:**
- Consumes: `data/para_rotular.csv`; `taxonomia.ROTULOS`.
- Produces:
  - `dividir_em_lotes(df: pd.DataFrame, tamanho: int = 150, seed: int = 2026) -> list[pd.DataFrame]` (embaralha; cada lote com `review_id, texto`).
  - `ler_booleano(valor) -> bool`: `True` para `True`, "true", "sim", "s", "1", 1; `False` para o resto.
  - `juntar_rotulos(esperados: pd.DataFrame, devolvidos: list[pd.DataFrame]) -> pd.DataFrame`: colunas `review_id, rotulo, duvida, grupo`; levanta `ValueError` com os ids em falta, repetidos, desconhecidos ou com rótulo inválido.
  - `concordancia(a: pd.Series, b: pd.Series) -> dict` com `acordo` (fração) e `kappa` (`sklearn.metrics.cohen_kappa_score`).
  - CLI `python -m triagem.rotulagem preparar` grava `data/lotes/lote_XX.csv`; `... juntar` lê `data/lotes/rotulos_XX.csv` e grava `data/rotulos_claude.csv`; `... consistencia-preparar` sorteia 200 do `dev` (`random_state=2026`) em `data/lotes/consistencia_XX.csv` (lotes de 100); `... consistencia-juntar` grava `data/rotulos_claude_consistencia.csv` e imprime acordo e kappa contra a primeira passada.

- [ ] **Step 1: Testes que falham**

```python
ESP = pd.DataFrame({"review_id": ["a", "b", "c"], "texto": ["x", "y", "z"], "grupo": ["dev", "aleatorio", "incerto"]})

def lote(ids, rot="outro", duv="false"):
    return pd.DataFrame({"review_id": ids, "rotulo": rot, "duvida": duv})

def test_juntar_ok():
    r = juntar_rotulos(ESP, [lote(["a", "b"]), lote(["c"], duv="sim")])
    assert list(r.columns) == ["review_id", "rotulo", "duvida", "grupo"]
    assert r.set_index("review_id").loc["c", "duvida"] == True

@pytest.mark.parametrize("devolvidos,trecho", [
    ([lote(["a", "b"])], "faltando: c"),
    ([lote(["a", "b", "c", "a"])], "repetidos: a"),
    ([lote(["a", "b", "c", "zz"])], "desconhecidos: zz"),
    ([lote(["a", "b"]), lote(["c"], rot="frete")], "rótulo inválido: c"),
])
def test_juntar_falha_com_ids(devolvidos, trecho):
    with pytest.raises(ValueError, match=trecho):
        juntar_rotulos(ESP, devolvidos)

@pytest.mark.parametrize("v,esperado", [("sim", True), ("true", True), ("1", True), (True, True), ("não", False), ("false", False), ("", False)])
def test_ler_booleano(v, esperado):
    assert ler_booleano(v) is esperado

def test_lotes_cobrem_tudo_sem_repetir():
    df = pd.DataFrame({"review_id": [f"r{i}" for i in range(320)], "texto": "t"})
    lotes = dividir_em_lotes(df, 150)
    assert [len(l) for l in lotes] == [150, 150, 20]
    assert sorted(pd.concat(lotes).review_id) == sorted(df.review_id)

def test_concordancia():
    r = concordancia(pd.Series(["a", "b", "a"]), pd.Series(["a", "b", "b"]))
    assert r["acordo"] == pytest.approx(2 / 3)
```
- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_rotulagem.py -q` → FAIL (`ModuleNotFoundError`).
- [ ] **Step 3: Implementar** as funções e a CLI acima. A mensagem do `ValueError` junta as partes que existirem no formato `"faltando: id1, id2; repetidos: ...; desconhecidos: ...; rótulo inválido: ..."`.
- [ ] **Step 4:** mesmo comando → PASS.
- [ ] **Step 5: Commit** — `git add src/triagem/rotulagem.py tests/test_rotulagem.py && git commit -m "Adiciona a preparação dos lotes e a checagem dos rótulos do Claude"`

---

### Task 4: Rotular com agentes (execução)

**Files:**
- Create: `data/rotulos_claude.csv`, `data/rotulos_claude_consistencia.csv`

- [ ] **Step 1:** `PYTHONPATH=src .venv/bin/python -m triagem.rotulagem preparar` → 20 lotes em `data/lotes/`.
- [ ] **Step 2: Lançar um agente por lote**, em paralelo (até 5 por vez), `subagent_type: general-purpose`, com este pedido (trocar `XX`):

```
Você vai rotular reclamações de e-commerce em português. Leia só o arquivo
/Users/mateus/Projetos/triagem-reclamacoes/data/lotes/lote_XX.csv (colunas review_id, texto).
Não abra nenhum outro arquivo do projeto, em especial data/ouro.csv, rotulagem/ e results/.

Guia de rotulagem:
<conteúdo de taxonomia.GUIA_ROTULAGEM, colado aqui>

Para cada linha, escolha exatamente uma categoria entre as 7 do guia e marque duvida=true
se ficou entre duas. Grave /Users/mateus/Projetos/triagem-reclamacoes/data/lotes/rotulos_XX.csv
com as colunas review_id,rotulo,duvida, uma linha por review_id do lote, na mesma ordem,
sem linhas a mais. Use um script Python só para escrever o CSV, com os rótulos que você
decidiu lendo cada texto; não use regras automáticas, palavras-chave nem modelos para decidir.
Responda só com o número de linhas gravadas.
```
- [ ] **Step 3:** `PYTHONPATH=src .venv/bin/python -m triagem.rotulagem juntar` → grava `data/rotulos_claude.csv` com 3.000 linhas. Se der `ValueError`, relançar só os lotes citados.
- [ ] **Step 4: Consistência.** `... consistencia-preparar`, lançar 2 agentes com o mesmo pedido apontando para `consistencia_XX.csv` e gravando `rotulos_consistencia_XX.csv`, depois `... consistencia-juntar` → imprime acordo e kappa; anotar no registro.
- [ ] **Step 5: Commit** — `git add data/rotulos_claude.csv data/rotulos_claude_consistencia.csv && git commit -m "Adiciona os rótulos do Claude para treino e desenvolvimento"`

---

### Task 5: Regras como variáveis e três candidatos

**Files:**
- Modify: `src/triagem/modelo.py`
- Test: `tests/test_modelo.py`

**Interfaces:**
- Consumes: `regras.REGRAS`, `regras.regras_que_disparam`.
- Produces:
  - `class VariaveisRegras(BaseEstimator, TransformerMixin)`: `transform(textos) -> scipy.sparse.csr_matrix` de forma `(n, len(REGRAS))`, 1 onde a regra dispara.
  - `CANDIDATOS = ("logistica", "svm", "nb")`.
  - `montar_candidato(nome: str) -> Pipeline`: passos `("tfidf", FeatureUnion([palavras, caracteres, ("regras", VariaveisRegras())]))` e `("clf", ...)`: `LogisticRegression(class_weight="balanced", max_iter=2000)`, `CalibratedClassifierCV(LinearSVC(class_weight="balanced"), cv=3)` ou `ComplementNB()`.
  - `GRADES = {"logistica": {"clf__C": [0.3, 1, 3, 10, 30]}, "svm": {"clf__estimator__C": [0.03, 0.1, 0.3, 1]}, "nb": {"clf__alpha": [0.1, 0.3, 1]}}`.
  - `palavras_que_pesaram` passa a aceitar o passo `clf` além de `logistica` e devolve `[]` quando o classificador não tem `coef_`.

- [ ] **Step 1: Testes que falham**

```python
def test_variaveis_regras():
    m = VariaveisRegras().transform(["não chegou", "xyz"])
    assert m.shape == (2, len(REGRAS)) and m[0].sum() >= 1 and m[1].sum() == 0

@pytest.mark.parametrize("nome", CANDIDATOS)
def test_candidato_tem_7_colunas(nome):
    m = montar_candidato(nome).fit(TEXTOS, ROTS)
    p = probabilidades(m, ["não chegou"])
    assert list(p.columns) == ROTULOS and p.loc[0, "outro"] == 0
```
- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_modelo.py -q` → FAIL (`ImportError`).
- [ ] **Step 3: Implementar.** As funções existentes (`montar_pipeline`, `treinar`, `probabilidades_fora_da_amostra`) continuam iguais para a supervisão fraca.
- [ ] **Step 4:** mesmo comando → PASS; suíte inteira verde.
- [ ] **Step 5: Commit** — `git commit -am "Adiciona as regras como variáveis e os três modelos candidatos"`

---

### Task 6: Escolha no desenvolvimento, fila e predições no ouro

**Files:**
- Create: `src/triagem/desenvolvimento.py`
- Modify: `src/triagem/triagem.py` (adicionar `decidir_modelo`)
- Test: `tests/test_desenvolvimento.py`

**Interfaces:**
- Consumes: `montar_candidato`, `GRADES`, `CANDIDATOS`, `probabilidades`, `palavras_que_pesaram` (Task 5); `escolher_limiar`, `sem_conteudo`, `Decisao` (`triagem.py`); `regras.rotular`; `data/rotulos_claude.csv`.
- Produces:
  - `triagem.decidir_modelo(probas: pd.Series, limiar: float, texto: str) -> Decisao`: `origem="modelo"`, `regra=None`; revisão com motivo `"texto sem conteúdo"` ou `"certeza baixa"`.
  - `FORMAS = {"A": None, "B0.1": 0.1, "B0.3": 0.3}` (peso dos rótulos das regras).
  - `montar_treino(rotulos: pd.DataFrame, pool: pd.DataFrame, peso_regras: Optional[float]) -> tuple[list[str], list[str], np.ndarray]`: textos, rótulos e pesos. Forma A: só `grupo != "dev"` com peso 1. Forma B: acrescenta as mensagens do pool que não estão em `rotulos` (nenhum grupo) e que as regras rotulam sem conflito, com o peso dado.
  - `comparar(rotulos, pool) -> pd.DataFrame` com `modelo, forma, f1_dev, params`, uma linha por par (candidato, forma): `GridSearchCV(montar_candidato(nome), GRADES[nome], scoring="f1_macro", cv=StratifiedKFold(5, shuffle=True, random_state=2026))` no treino, passando `clf__sample_weight`; F1 macro no dev com o melhor estimador.
  - CLI `python -m triagem.desenvolvimento`: roda `comparar`, escolhe o maior `f1_dev`, calcula `limiar = escolher_limiar(probas_dev, rotulos_dev)`, grava `results/desenvolvimento.md` (todas as linhas), `results/modelo.joblib` (`modelo, limiar, nome, forma, f1_dev`), `results/triagem.csv` (pool inteiro, colunas iguais às da supervisão fraca, com `origem="modelo"`) e `results/preds/ouro__rotulos-claude__<nome>__<forma>.jsonl` (`review_id, pred, latencia_s, revisao`; textos de `dados.amostra_ouro(dados.reclamacoes())`). Apaga antes os `ouro__rotulos-claude__*.jsonl` antigos.

- [ ] **Step 1: Testes que falham**

```python
# TEXTOS, ROTS e p() iguais aos de tests/test_triagem.py, definidos também aqui.
def test_decidir_modelo():
    assert decidir_modelo(p(outro=0.9, item_faltando=0.1), 0.8, "não gostei").revisao is False
    assert decidir_modelo(p(outro=0.6, item_faltando=0.4), 0.8, "não gostei").motivo_revisao == "certeza baixa"
    assert decidir_modelo(p(outro=0.99), 0.8, "123").motivo_revisao == "texto sem conteúdo"

def test_montar_treino_formas():
    rot = pd.DataFrame({"review_id": ["a", "b", "d"], "rotulo": ["outro", "item_faltando", "outro"], "grupo": ["aleatorio", "incerto", "dev"]})
    pool = pd.DataFrame({"review_id": ["a", "b", "c", "d", "e"], "texto": ["xyz", "só veio um", "não chegou", "ok", "abc"]})
    t, r, w = montar_treino(rot, pool, None)
    assert len(t) == 2 and (w == 1).all()
    t, r, w = montar_treino(rot, pool, 0.3)
    assert len(t) == 3 and r[-1] == "nao_recebido_atraso" and w[-1] == pytest.approx(0.3)

@pytest.mark.parametrize("nome", CANDIDATOS)
def test_peso_chega_ao_classificador(nome):
    w = np.r_[np.ones(30), np.full(30, 0.1)]
    busca = GridSearchCV(montar_candidato(nome), GRADES[nome], cv=3)
    busca.fit(TEXTOS, ROTS, clf__sample_weight=w)
    assert busca.best_estimator_ is not None
```
- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_desenvolvimento.py -q` → FAIL.
- [ ] **Step 3: Implementar** `decidir_modelo`, `montar_treino`, `comparar` e o `main`. O dev nunca entra no treino.
- [ ] **Step 4:** mesmo comando → PASS; rodar `PYTHONPATH=src .venv/bin/python -m triagem.desenvolvimento` e conferir os quatro arquivos gravados e as 9 linhas de `results/desenvolvimento.md`.
- [ ] **Step 5: Commit** — `git add src tests results/desenvolvimento.md results/triagem.csv results/preds/ouro__rotulos-claude__*.jsonl && git commit -m "Escolhe o modelo no desenvolvimento e gera a fila com os rótulos do Claude"`

---

### Task 7: Makefile e avaliação

**Files:**
- Modify: `Makefile`, `src/triagem/avaliar.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: `results/modelo.joblib` (`f1_dev`, `nome`, `forma`), `results/preds/*.jsonl`.
- Produces: `avaliar.secao_aviso(ouro: pd.DataFrame) -> list[str]` com a linha de aviso; `resultados.md` ganha o F1 no desenvolvimento do modelo escolhido.

- [ ] **Step 1: Teste que falha**

```python
def test_secao_aviso_conta_rotulos_do_claude():
    ouro = pd.DataFrame({"fonte": ["mateus", "claude", "claude"]})
    texto = "\n".join(avaliar.secao_aviso(ouro))
    assert "2 das 3" in texto and "53" not in texto
```
- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_pipeline.py -q` → FAIL (`AttributeError`).
- [ ] **Step 3: Implementar.** `secao_aviso`: "Atenção: N das M mensagens do ouro foram rotuladas pelo Claude, que também rotulou o treino do modelo novo. A comparação honesta com o Qwen é na coluna das rotuladas pelo Mateus." `main` acrescenta essa seção e, se `results/modelo.joblib` existir, a linha "F1 macro no desenvolvimento do modelo escolhido (<nome>, forma <forma>): X". Makefile: `selecionar` (fora do `tudo`), `supervisao` (o antigo `triagem`), `treinar` (`python -m triagem.desenvolvimento`), `tudo: testes regras supervisao treinar avaliar`.
- [ ] **Step 4:** `make tudo` → testes verdes e `results/resultados.md` com a linha `rotulos-claude/...`.
- [ ] **Step 5: Commit** — `git add Makefile src tests results && git commit -m "Avalia o modelo novo no ouro e ajusta o make tudo"`

---

### Task 8: Documentação e revisão

**Files:**
- Modify: `DECISOES.md`, `README.md`, `CLAUDE.md` (local)

- [ ] **Step 1: `DECISOES.md`.** Nova seção "Rótulos do Claude" (por que, como os 3.000 foram escolhidos, o guia, quem rotulou e em qual modelo, consistência com acordo e kappa, o viés no ouro). Reescrever a seção 2 ("LLM só para rotular uma vez, nunca na triagem"). Resultados novos com a tabela de `results/desenvolvimento.md` e a do ouro. A supervisão fraca vira seção de histórico. Relatar se passou ou não dos 60,5% nas 53.
- [ ] **Step 2: README.** Abertura: "sem LLM na triagem; rótulos de treino feitos uma vez pelo Claude". Resultados novos, comparação com Qwen nas 53 em destaque, aviso dos 247.
- [ ] **Step 3: `CLAUDE.md`.** Comandos novos (`make selecionar`, `make treinar`), número de testes, abordagem atual.
- [ ] **Step 4:** `make tudo && grep -c "—" README.md DECISOES.md` → verde e zero.
- [ ] **Step 5:** `/code-review` do branch; corrigir o que for confirmado.
- [ ] **Step 6: Commit** — `git add DECISOES.md README.md && git commit -m "Documenta o treino com rótulos do Claude e os resultados"`
