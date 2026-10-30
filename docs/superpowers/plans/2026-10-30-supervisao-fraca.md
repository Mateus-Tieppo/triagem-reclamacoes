# Triagem por supervisão fraca: plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trocar a rotulagem por LLM por regras legíveis (supervisão fraca) + regressão logística, com fila de revisão humana, explicação e avaliação honesta, tudo local e sem LLM.

**Architecture:** `normalizar` limpa o texto e é usado dentro do TF-IDF, então treino e uso tratam o texto igual. `regras` vota uma categoria por mensagem do pool de treino; `modelo` aprende com esses votos; `triagem` combina regra e modelo numa decisão final com motivo de revisão, grava `results/triagem.csv` e as predições no ouro; `avaliar` compara tudo no ouro.

**Tech Stack:** Python 3.9+, pandas, numpy, scikit-learn, matplotlib, joblib, pytest. Nada novo.

**Spec:** `docs/superpowers/specs/2026-10-30-supervisao-fraca-design.md`

## Global Constraints

- Nenhuma LLM em nenhuma etapa nova, nem local. Não importar `triagem.llm`, `triagem.rodar_llm` nem `triagem.prompts` nos módulos novos.
- `data/ouro.csv` só é lido em `avaliar.py`. Para excluir o ouro do treino, use os ids de `dados.amostra_ouro(dados.reclamacoes())`, que não carrega rótulos.
- Regras, limiar e `C` nunca são escolhidos olhando o ouro. Regras são escritas lendo `amostra_desenvolvimento` (Task 2) e `data/fewshot.csv`.
- Python 3.9: `from __future__ import annotations` em todo módulo novo; nada de `match` nem `X | Y` em tempo de execução.
- Só pandas, numpy, scikit-learn, matplotlib e joblib.
- Testes não chamam rede nem Ollama.
- `SEED = 42` (`dados.SEED`) em toda aleatoriedade.
- Os 53 rótulos com `fonte == mateus` não são alterados.
- Textos do Mateus (README, DECISOES, mensagens de commit): sem travessões; todo número vem de código rodado.
- Trabalhar no branch `supervisao-fraca`. Não fazer push sem o Mateus pedir. Rodar `/code-review` antes do commit final (Task 7).

## Review Focus

1. Texto vazio depois da normalização (só emoji, só pontuação, só número): nada quebra, o modelo decide e a mensagem vai para revisão por certeza baixa. Teste na Task 4.
2. Negação e falso positivo: "chegou rápido mas veio quebrado" não pode disparar atraso; "não veio a nota fiscal" não pode virar `item_faltando`. Testes na Task 2.
3. Variações de escrita: "NÃO CHEGOU", "nao chegou", "naõ chegou ainda", "ñ chegou" disparam a mesma regra. Teste na Task 2.
4. Categoria sem nenhum rótulo de regra no treino: as probabilidades ainda trazem as 7 categorias (a ausente com 0) e `decidir` não quebra. Teste na Task 3.
5. Vazamento do ouro: nenhum `review_id` do ouro nem do few-shot aparece em `results/triagem.csv` nem entra no treino. Teste na Task 4.

---

### Task 1: Normalização do texto

**Files:**
- Create: `src/triagem/normalizar.py`
- Test: `tests/test_normalizar.py`

**Interfaces:**
- Produces: `normalizar(texto: str) -> str`; constantes `MARCA_LINK = "_link_"`, `MARCA_NUM = "_num_"`.

- [ ] **Step 0: Criar o branch**

Run: `git switch -c supervisao-fraca`

- [ ] **Step 1: Escrever os testes que falham**

```python
@pytest.mark.parametrize("entrada,esperado", [
    ("NÃO Chegou", "nao chegou"),
    ("péssimooooo", "pessimo"),
    ("muuuito ruim!!!", "muito ruim!"),
    ("veja http://x.com/a e mail@x.com", "veja _link_ e _link_"),
    ("pedido 12345 de 20/12/2017 R$ 59,90", "pedido _num_ de _num_ r$ _num_"),
    ("  linha1\n\nlinha2\t ", "linha1 linha2"),
    ("", ""),
    ("😡😡😡", "😡"),
])
def test_normalizar(entrada, esperado):
    assert normalizar(entrada) == esperado

def test_normalizar_e_idempotente():
    t = "NÃO chegouuu, pedido 123 http://a.b"
    assert normalizar(normalizar(t)) == normalizar(t)

def test_normalizar_preserva_letras_duplas():
    assert normalizar("carro passou") == "carro passou"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/python -m pytest tests/test_normalizar.py -q`
Expected: FAIL com `ModuleNotFoundError: triagem.normalizar`

- [ ] **Step 3: Implementar `normalizar(texto: str) -> str`**

Ordem: links/e-mails → `_link_`; minúsculas; sem acentos (`unicodedata` NFKD sem marcas combinantes); sequências de dígitos com `/ . , : -` entre eles → `_num_`; qualquer caractere repetido 3+ vezes → um; espaços colapsados e `strip`. O marcador não pode ser afetado pelas etapas seguintes.

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/bin/python -m pytest tests/test_normalizar.py -q`
Expected: todos passam

- [ ] **Step 5: Commit**

```bash
git add src/triagem/normalizar.py tests/test_normalizar.py
git commit -m "Adiciona a normalização do texto usada em regras e modelo"
```

---

### Task 2: Regras legíveis e relatório de cobertura

**Files:**
- Create: `src/triagem/regras.py`
- Modify: `src/triagem/dados.py` (adicionar `pool_de_treino()` e `amostra_desenvolvimento()`)
- Test: `tests/test_regras.py`

**Interfaces:**
- Consumes: `normalizar` (Task 1); `dados.reclamacoes`, `dados.amostra_ouro`, `dados.pool_treino`, `dados.ARQUIVO_FEWSHOT`.
- Produces:
  - `@dataclass(frozen=True) class Regra: nome: str; categoria: str; padrao: str` (regex sobre texto normalizado).
  - `REGRAS: list[Regra]`.
  - `PRIORIDADE: list[str] = ["nao_recebido_atraso", "item_faltando", "produto_errado", "defeito_qualidade", "cobranca_cancelamento", "atendimento_loja", "outro"]`; `CATEGORIAS_ORIGEM = PRIORIDADE[:4]`.
  - `@dataclass(frozen=True) class Voto: rotulo: Optional[str]; regra: Optional[str]; conflito: bool; categorias: tuple[str, ...]`.
  - `rotular(texto: str) -> Voto` (normaliza dentro).
  - `relatorio(textos: list[str]) -> str` (Markdown).
  - `dados.pool_de_treino() -> pd.DataFrame` (colunas `review_id`, `order_id`, `texto`): `pool_treino(reclamacoes(), ids do amostra_ouro, ids do fewshot)`.
  - `dados.amostra_desenvolvimento(n: int = 200, seed: int = SEED) -> pd.DataFrame`: amostra do `pool_de_treino()` para ler e escrever regras.
  - CLI: `python -m triagem.regras` grava `results/regras.md`; `python -m triagem.regras --amostra 200` imprime a amostra de desenvolvimento.

- [ ] **Step 1: Escrever os testes que falham**

```python
@pytest.mark.parametrize("texto,rotulo", [
    ("Até hoje não recebi o produto", "nao_recebido_atraso"),
    ("NÃO CHEGOU", "nao_recebido_atraso"),
    ("naõ chegou ainda", "nao_recebido_atraso"),
    ("ñ chegou", "nao_recebido_atraso"),
    ("comprei 2 e só veio 1", "item_faltando"),
    ("veio a cor errada", "produto_errado"),
    ("diferente do anúncio", "produto_errado"),
    ("chegou rápido mas veio quebrado", "defeito_qualidade"),
    ("quero meu estorno", "cobranca_cancelamento"),
    ("a loja não responde meus emails", "atendimento_loja"),
    ("produto ótimo, entrega rápida", "outro"),
])
def test_rotular_categoria(texto, rotulo):
    assert rotular(texto).rotulo == rotulo

def test_sem_regra_fica_sem_rotulo():
    v = rotular("xyz abc qwerty")
    assert v.rotulo is None and v.regra is None and not v.conflito

def test_consequencia_perde_para_origem():
    v = rotular("não chegou e a loja não responde")
    assert v.rotulo == "nao_recebido_atraso" and not v.conflito

def test_duas_origens_marcam_conflito_e_seguem_prioridade():
    v = rotular("veio quebrado e faltou um item")
    assert v.conflito and v.rotulo == "item_faltando"

def test_outro_so_quando_nada_mais_dispara():
    assert rotular("produto ótimo mas não chegou").rotulo == "nao_recebido_atraso"

def test_nota_fiscal_nao_e_item_faltando():
    assert rotular("não veio a nota fiscal").rotulo != "item_faltando"

def test_regras_validas():
    nomes = [r.nome for r in REGRAS]
    assert len(nomes) == len(set(nomes))
    assert {r.categoria for r in REGRAS} == set(PRIORIDADE)
    for r in REGRAS:
        re.compile(r.padrao)

def test_pool_de_treino_sem_ouro_nem_fewshot():
    pool = dados.pool_de_treino()
    ouro = set(dados.amostra_ouro(dados.reclamacoes()).review_id)
    fs = set(pd.read_csv(dados.ARQUIVO_FEWSHOT).review_id)
    assert not (ouro | fs) & set(pool.review_id)

def test_relatorio_tem_cobertura():
    md = relatorio(["não chegou", "veio quebrado", "xyz"])
    assert "Sem rótulo" in md and "nao_recebido_atraso" in md
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/python -m pytest tests/test_regras.py -q`
Expected: FAIL com `ModuleNotFoundError: triagem.regras`

- [ ] **Step 3: Implementar `dados.pool_de_treino` e `dados.amostra_desenvolvimento`; incluir `order_id` nas colunas de `reclamacoes()`**

`reclamacoes()` passa a devolver `review_id, order_id, review_score, texto`. Os testes antigos continuam passando.

- [ ] **Step 4: Ler a amostra de desenvolvimento e escrever as regras**

Run: `PYTHONPATH=src .venv/bin/python -m triagem.regras --amostra 200` (e também com `seed` 1 e 2, para ver 600 mensagens). Escrever `REGRAS` com uma regra por padrão de frase, nomes curtos (`nao_recebi`, `atrasou`, `so_veio_um`, `cor_errada`...). Cada regra precisa ser legível em uma linha. Não abrir `data/ouro.csv`.

- [ ] **Step 5: Implementar `rotular` e `relatorio`**

`rotular`: normaliza; coleta as categorias que disparam; `conflito` = duas ou mais categorias distintas de `CATEGORIAS_ORIGEM` dispararam; `outro` só conta se nenhuma outra disparar; `rotulo` = primeira categoria de `PRIORIDADE` com voto; `regra` = nome da primeira regra dessa categoria que disparou. `relatorio`: por categoria e por regra, quantas mensagens; linhas "Sem rótulo" e "Com conflito", com contagem e percentual.

- [ ] **Step 6: Rodar e ver passar; gerar o relatório**

Run: `.venv/bin/python -m pytest tests/test_regras.py -q && PYTHONPATH=src .venv/bin/python -m triagem.regras`
Expected: testes passam; `results/regras.md` gravado. Conferir que nenhuma categoria tem zero mensagens; se tiver, voltar ao Step 4.

- [ ] **Step 7: Commit**

```bash
git add src/triagem/regras.py src/triagem/dados.py tests/test_regras.py results/regras.md
git commit -m "Adiciona as regras legíveis que rotulam o pool de treino"
```

---

### Task 3: Modelo (TF-IDF + regressão logística) e explicação

**Files:**
- Create: `src/triagem/modelo.py`
- Test: `tests/test_modelo.py`

**Interfaces:**
- Consumes: `normalizar` (Task 1); `taxonomia.ROTULOS`.
- Produces:
  - `montar_pipeline(C: float = 1.0) -> Pipeline`: `FeatureUnion` com `("palavras", TfidfVectorizer(preprocessor=normalizar, ngram_range=(1, 2), min_df=2, sublinear_tf=True))` e `("caracteres", TfidfVectorizer(preprocessor=normalizar, analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True))`, seguido de `("logistica", LogisticRegression(class_weight="balanced", max_iter=2000))`.
  - `treinar(textos: list[str], rotulos: list[str]) -> GridSearchCV`: `C` em `[0.3, 1, 3, 10]`, `scoring="f1_macro"`, `StratifiedKFold(5, shuffle=True, random_state=42)`.
  - `probabilidades(modelo, textos: list[str]) -> pd.DataFrame`: colunas exatamente `ROTULOS`, classe ausente no treino = 0.
  - `probabilidades_fora_da_amostra(textos, rotulos, C: float) -> pd.DataFrame`: mesmo formato, via `cross_val_predict(method="predict_proba")` com o mesmo `StratifiedKFold`.
  - `palavras_que_pesaram(modelo, texto: str, categoria: str, k: int = 3) -> list[str]`: termos do vetorizador `palavras` com maior coeficiente × peso TF-IDF positivo para a categoria; lista vazia se a categoria não existe no modelo.

- [ ] **Step 1: Escrever os testes que falham**

```python
TEXTOS = ["não chegou ainda"] * 20 + ["veio quebrado com defeito"] * 20 + ["faltou um item no pacote"] * 20
ROTS = ["nao_recebido_atraso"] * 20 + ["defeito_qualidade"] * 20 + ["item_faltando"] * 20

def test_aprende_padrao_simples():
    m = treinar(TEXTOS, ROTS).best_estimator_
    assert list(m.predict(["o pedido NÃO chegou", "chegou com defeito"])) == ["nao_recebido_atraso", "defeito_qualidade"]

def test_probabilidades_tem_todas_as_categorias():
    m = treinar(TEXTOS, ROTS).best_estimator_
    p = probabilidades(m, ["não chegou"])
    assert list(p.columns) == ROTULOS
    assert p.loc[0, "outro"] == 0 and p.loc[0, "produto_errado"] == 0
    assert p.loc[0].sum() == pytest.approx(1)

def test_fora_da_amostra_mesmo_formato():
    p = probabilidades_fora_da_amostra(TEXTOS, ROTS, C=1.0)
    assert p.shape == (60, len(ROTULOS))

def test_palavras_que_pesaram():
    m = treinar(TEXTOS, ROTS).best_estimator_
    assert "quebrado" in palavras_que_pesaram(m, "veio quebrado", "defeito_qualidade")
    assert palavras_que_pesaram(m, "veio quebrado", "outro") == []
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/python -m pytest tests/test_modelo.py -q`
Expected: FAIL com `ModuleNotFoundError: triagem.modelo`

- [ ] **Step 3: Implementar as funções acima em `src/triagem/modelo.py`**

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/bin/python -m pytest tests/test_modelo.py -q`
Expected: todos passam

- [ ] **Step 5: Commit**

```bash
git add src/triagem/modelo.py tests/test_modelo.py
git commit -m "Adiciona o modelo de regressão logística e a explicação por palavras"
```

---

### Task 4: Decisão final, fila de revisão e predições no ouro

**Files:**
- Create: `src/triagem/triagem.py`
- Test: `tests/test_triagem.py`

**Interfaces:**
- Consumes: `regras.rotular`, `regras.Voto` (Task 2); `modelo.*` (Task 3); `dados.pool_de_treino`, `dados.amostra_ouro`, `dados.reclamacoes`.
- Produces:
  - `escolher_limiar(probas: pd.DataFrame, rotulos: list[str], alvo: float = 0.85) -> float`: menor `t` em `0.00, 0.01, ..., 0.99` em que as linhas com `max(proba) >= t` têm argmax igual ao rótulo em pelo menos `alvo`; se nenhum atingir, `0.99`.
  - `@dataclass(frozen=True) class Decisao: categoria: str; origem: str; regra: Optional[str]; certeza: float; revisao: bool; motivo_revisao: str`.
  - `decidir(voto: Voto, probas: pd.Series, limiar: float) -> Decisao`.
  - CLI `python -m triagem.triagem`: grava `results/triagem.csv`, `results/modelo.joblib` (`{"modelo": ..., "limiar": ..., "C": ...}`) e três arquivos em `results/preds/`: `ouro__supervisao-fraca__regras__sozinhas.jsonl`, `ouro__supervisao-fraca__logistica__sozinho.jsonl`, `ouro__supervisao-fraca__hibrido__final.jsonl`.

Regras de `decidir` (fixadas pelo spec):
- `voto.rotulo` e não `voto.conflito`: `categoria = voto.rotulo`, `origem = "regra"`, `certeza = probas[voto.rotulo]`; revisão só se `argmax(probas) != voto.rotulo`, motivo `"regra e modelo discordam"`.
- Senão: `categoria = argmax(probas)`, `origem = "modelo"`, `certeza = max(probas)`, `regra = voto.regra` se houve conflito; motivos, unidos por `"; "`: `"conflito entre regras"` se `voto.conflito`; `"certeza baixa"` se `certeza < limiar`.

- [ ] **Step 1: Escrever os testes que falham**

```python
# TEXTOS e ROTS iguais aos da Task 3, definidos também neste arquivo de teste.
def p(**kw):
    s = pd.Series(0.0, index=ROTULOS); s.update(pd.Series(kw)); return s

def test_regra_e_modelo_concordam():
    d = decidir(Voto("item_faltando", "so_veio_um", False, ("item_faltando",)), p(item_faltando=0.7, outro=0.3), 0.5)
    assert (d.categoria, d.origem, d.revisao, d.certeza) == ("item_faltando", "regra", False, 0.7)

def test_regra_e_modelo_discordam_vai_para_revisao():
    d = decidir(Voto("item_faltando", "so_veio_um", False, ("item_faltando",)), p(defeito_qualidade=0.8, item_faltando=0.2), 0.5)
    assert d.categoria == "item_faltando" and d.revisao and d.motivo_revisao == "regra e modelo discordam"

def test_sem_regra_modelo_decide_com_certeza_baixa():
    d = decidir(Voto(None, None, False, ()), p(outro=0.4, atendimento_loja=0.35, defeito_qualidade=0.25), 0.6)
    assert (d.categoria, d.origem, d.revisao, d.motivo_revisao) == ("outro", "modelo", True, "certeza baixa")

def test_conflito_modelo_decide_e_revisa():
    v = Voto("item_faltando", "faltou", True, ("item_faltando", "defeito_qualidade"))
    d = decidir(v, p(defeito_qualidade=0.9, item_faltando=0.1), 0.5)
    assert d.origem == "modelo" and d.categoria == "defeito_qualidade" and d.motivo_revisao == "conflito entre regras"

def test_texto_vazio_nao_quebra():
    m = treinar(TEXTOS, ROTS).best_estimator_
    d = decidir(rotular("😡😡"), probabilidades(m, ["😡😡"]).iloc[0], 0.9)
    assert d.revisao and d.categoria in ROTULOS

def test_escolher_limiar():
    probas = pd.DataFrame([p(outro=0.9), p(outro=0.6), p(item_faltando=0.55)])
    assert escolher_limiar(probas, ["outro", "item_faltando", "outro"], alvo=0.85) == pytest.approx(0.61)

def test_triagem_csv_sem_ouro(tmp_path, monkeypatch):
    # roda o main com um pool pequeno falso e confere colunas e ausência de ids do ouro
    ...
```

O último teste: usar `monkeypatch` em `dados.pool_de_treino` (60 linhas de `TEXTOS` com ids `t0..t59`) e em `dados.amostra_ouro` (3 linhas com ids `o0..o2`), apontar `dados.RAIZ` para `tmp_path`, rodar `main()`, e afirmar que `triagem.csv` tem exatamente as colunas `review_id, texto, categoria, origem, regra, certeza, revisao, motivo_revisao, palavras`, 60 linhas, nenhum id começando com `o`, e que os três `.jsonl` do ouro têm 3 linhas com `review_id`, `pred`, `latencia_s` (o híbrido também com `revisao`).

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/python -m pytest tests/test_triagem.py -q`
Expected: FAIL com `ModuleNotFoundError: triagem.triagem`

- [ ] **Step 3: Implementar `escolher_limiar`, `decidir` e `main`**

`main`: pool → `rotular` em tudo → treino = linhas com rótulo e sem conflito → `treinar` (pega `best_params_["logistica__C"]`) → `probabilidades_fora_da_amostra` para as linhas de treino e `probabilidades` do modelo final para as demais → `escolher_limiar` sobre as fora da amostra → `decidir` linha a linha → coluna `palavras` = `palavras_que_pesaram(modelo_final, texto, categoria)` unidas por `", "` → CSV. No ouro (textos de `amostra_ouro`, sem rótulos): "regras sozinhas" = `voto.rotulo or "outro"`; "logística sozinho" = argmax; "híbrido" = `decidir`. Latência por mensagem medida com `time.perf_counter`. Imprimir tamanho do treino, `C`, F1 da validação cruzada, limiar e taxa de revisão.

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/bin/python -m pytest tests/test_triagem.py -q`
Expected: todos passam

- [ ] **Step 5: Rodar de verdade**

Run: `PYTHONPATH=src .venv/bin/python -m triagem.triagem`
Expected: grava `results/triagem.csv` (cerca de 10.450 linhas) e os três `.jsonl`; imprime limiar e taxa de revisão.

- [ ] **Step 6: Commit**

```bash
git add src/triagem/triagem.py tests/test_triagem.py results/triagem.csv results/preds/ouro__supervisao-fraca__*.jsonl
git commit -m "Adiciona a decisão final com fila de revisão e as predições no ouro"
```

---

### Task 5: Conferência de atraso com datas reais (opcional)

**Files:**
- Create: `src/triagem/verdade.py`
- Test: `tests/test_verdade.py`

**Interfaces:**
- Consumes: `results/triagem.csv` (Task 4); `dados.reclamacoes` (com `order_id`).
- Produces: `ARQUIVO_PEDIDOS = RAIZ / "data" / "raw" / "olist_orders_dataset.csv"`; `conferir_atraso(triagem: pd.DataFrame, pedidos: pd.DataFrame) -> dict` com chaves `n_atraso`, `pct_atrasado_entre_atraso`, `pct_atrasado_geral`; um pedido conta como atrasado se `order_status != "delivered"` ou `order_delivered_customer_date > order_estimated_delivery_date`.

- [ ] **Step 1: Teste que falha**

```python
def test_conferir_atraso():
    tri = pd.DataFrame({"review_id": ["a", "b", "c"], "categoria": ["nao_recebido_atraso", "nao_recebido_atraso", "outro"], "order_id": ["1", "2", "3"]})
    ped = pd.DataFrame({"order_id": ["1", "2", "3"], "order_status": ["delivered", "canceled", "delivered"],
                        "order_delivered_customer_date": ["2018-01-10", None, "2018-01-01"],
                        "order_estimated_delivery_date": ["2018-01-05", "2018-01-05", "2018-01-05"]})
    r = conferir_atraso(tri, ped)
    assert r["n_atraso"] == 2 and r["pct_atrasado_entre_atraso"] == 1.0 and r["pct_atrasado_geral"] == pytest.approx(2 / 3)
```

- [ ] **Step 2: Rodar e ver falhar** — `.venv/bin/python -m pytest tests/test_verdade.py -q`, FAIL por módulo ausente.
- [ ] **Step 3: Implementar `conferir_atraso`** (o `order_id` vem de juntar `triagem` com `dados.reclamacoes()` por `review_id` quando não estiver presente).
- [ ] **Step 4: Rodar e ver passar** — mesmo comando, PASS.
- [ ] **Step 5: Commit**

```bash
git add src/triagem/verdade.py tests/test_verdade.py
git commit -m "Adiciona a conferência de atraso com as datas reais de entrega"
```

---

### Task 6: Avaliação e Makefile

**Files:**
- Modify: `src/triagem/avaliar.py` (`avaliar`, `main`)
- Modify: `Makefile`
- Test: `tests/test_pipeline.py` (novo teste)

**Interfaces:**
- Consumes: os `.jsonl` da Task 4; `verdade.conferir_atraso` e `verdade.ARQUIVO_PEDIDOS` (Task 5); `results/triagem.csv`; `results/regras.md`.
- Produces: `avaliar(...)` ganha `taxa_revisao` e `f1_aceitas` (F1 macro só nas linhas com `revisao == False`), ambos `nan` quando o `.jsonl` não tem a coluna `revisao`.

- [ ] **Step 1: Teste que falha**

```python
def test_avaliar_com_revisao():
    ouro = pd.DataFrame({"review_id": ["a", "b"], "rotulo": ["outro", "item_faltando"], "duvida": [False, False]})
    preds = pd.DataFrame({"review_id": ["a", "b"], "pred": ["outro", "outro"], "latencia_s": [0.0, 0.0], "revisao": [False, True]})
    r = avaliar.avaliar(ouro, preds)
    assert r["taxa_revisao"] == 0.5 and r["f1_aceitas"] == pytest.approx(1.0)
```

- [ ] **Step 2: Rodar e ver falhar** — `.venv/bin/python -m pytest tests/test_pipeline.py::test_avaliar_com_revisao -q`, FAIL com `KeyError`.
- [ ] **Step 3: Implementar** as duas métricas; em `main`, colunas "Revisão" e "F1 sem revisão" (com "-" quando `nan`); ao fim do `resultados.md`, uma seção com cobertura das regras (linhas "Sem rótulo" e "Com conflito" copiadas de `results/regras.md`) e, se `ARQUIVO_PEDIDOS` existir, a conferência de atraso; se não existir, uma linha dizendo que foi pulada.
- [ ] **Step 4: Atualizar o `Makefile`**

```make
regras: instalar
	$(PY) -m triagem.regras

triagem: instalar
	$(PY) -m triagem.triagem

tudo: testes regras triagem avaliar
```

Manter `modelos`, `llm`, `prata` e `baseline` como estão, fora do `tudo`, e adicionar `regras triagem` ao `.PHONY`.

- [ ] **Step 5: Rodar tudo**

Run: `make tudo`
Expected: testes passam; `results/resultados.md` com as linhas `supervisao-fraca/...` ao lado das referências de LLM e SVM.

- [ ] **Step 6: Commit**

```bash
git add src/triagem/avaliar.py Makefile tests/test_pipeline.py results/resultados.md results/matriz__supervisao-fraca__*.png
git commit -m "Avalia regras, modelo e híbrido no ouro e roda tudo sem Ollama"
```

---

### Task 7: Documentação e revisão final

**Files:**
- Create: `DECISOES.md`
- Modify: `README.md`, `CLAUDE.md` (local, fora do git)

- [ ] **Step 1: Escrever `DECISOES.md`** no formato do `DECISOES.md` do Fila Viva (sumário numerado). Seções: a decisão central ("regras legíveis rotulam, modelo generaliza, humano na dúvida"); por que não usar LLM para rotular; a normalização; as regras e a prioridade (tabela com cada regra, categoria e cobertura de `results/regras.md`); o modelo e a validação cruzada; o limiar e a fila de revisão (valor e taxa saídos da Task 4); resultados (tabela de `results/resultados.md`, incluindo quando o híbrido perde para alguma referência); a conferência de atraso ou que ela foi pulada; limitações: sem conjunto de desenvolvimento rotulado à mão, os 247 rótulos do ouro feitos pelo Claude, o modelo aprende os erros das regras; o que ficou de fora (ferramenta, multirrótulo, embeddings); "quem fez o quê" (regras escritas pelo Claude, revisáveis pelo Mateus). Números só de saídas reais.
- [ ] **Step 2: Reescrever o `README.md`** em torno da supervisão fraca: problema, como funciona (as quatro peças), resultados, como rodar (`make tudo` sem Ollama), comparação com LLM como seção à parte, licença e ferramentas. Sem travessões; sem citar programa ou empresa; manter o selo do CI e a seção de dados da Olist.
- [ ] **Step 3: Atualizar a seção "Próximos passos" e os comandos do `CLAUDE.md`** local: `make tudo` sem Ollama, número atual de testes, próximo passo = a ferramenta (parte 3).
- [ ] **Step 4: Verificar**

Run: `make tudo && grep -c "—" README.md DECISOES.md`
Expected: tudo passa; zero travessões nos dois arquivos.

- [ ] **Step 5: Rodar `/code-review`** sobre o branch e corrigir o que for confirmado.
- [ ] **Step 6: Commit**

```bash
git add DECISOES.md README.md
git commit -m "Documenta as decisões e reescreve o README para a supervisão fraca"
```
