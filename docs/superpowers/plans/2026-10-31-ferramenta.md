# Central de triagem: plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publicar na Vercel uma central de triagem com painel, rodando o modelo clássico no navegador, idêntico ao Python, sobre as 7.451 reclamações que o modelo nunca viu.

**Architecture:** Dois scripts Python exportam o modelo (`web/public/modelo.json`), os dados do painel (`web/public/painel.json`) e as referências de paridade (`web/tests/fixtures/paridade.json`). Uma app Next.js com `output: 'export'` em `web/` reimplementa a predição em TypeScript, testada contra as referências, e mostra Painel, Filas, Revisão, Triar as minhas e Sobre.

**Tech Stack:** Python (scikit-learn, já no projeto); Next.js 16 (App Router, exportação estática), React, TypeScript, Vitest 5, Playwright 1.64; deploy na Vercel.

**Spec:** `docs/superpowers/specs/2026-10-31-ferramenta-design.md`

## Global Constraints

- Custo zero: sem servidor, sem API paga, sem banco; nada do usuário sai do navegador.
- Python novo compatível com 3.9 (`from __future__ import annotations`); o `joblib` lido é o gerado pelo próprio projeto.
- Nenhum LLM na ferramenta. Só o modelo de `results/modelo.joblib` exportado.
- Painel só com mensagens nunca vistas: pool (`dados.pool_de_treino()`) menos os ids de `data/rotulos_claude.csv` (3.000). O conjunto de teste (300) não entra no painel.
- Paridade: mesma categoria que o Python em 100% das referências; probabilidades iguais até 1e-3.
- Premissa de tempo: 30 segundos por mensagem, escrita na tela e ajustável.
- Correções (mover de fila) só no `localStorage`; a app funciona se ele falhar.
- Funciona a 375 px de largura sem rolagem horizontal; contraste AA, foco visível, teclado, `prefers-reduced-motion`.
- Antes de usar uma biblioteca nova, consultar a documentação atual no Context7.
- Visual: direção definida com `ui-ux-pro-max` e `impeccable` (Task 5) e fechada com `/impeccable polish` (Task 10). Sem cara de template de IA.
- React com `vercel-react-best-practices` e `vercel-composition-patterns`; animações com GSAP (`useGSAP`) só se agregarem, respeitando `prefers-reduced-motion`.
- Textos sem travessões, sem citar programa nem empresa; números só dos dados.
- Branch `ferramenta`; sem push sem o Mateus pedir (o deploy da Task 11 foi aprovado no design).

## Review Focus

1. Texto vazio, só emoji ou só número em "Triar as minhas": não quebra; vai para revisão com "texto sem conteúdo". Teste na Task 4.
2. CSV exportado do Excel brasileiro (separador `;`, BOM, aspas com quebra de linha, coluna de texto com outro nome): lê ou mostra um erro claro dizendo qual coluna escolher. Teste na Task 8.
3. Colar milhares de linhas: a triagem não trava a tela (processa em lotes e mostra progresso); 1.000 mensagens em menos de 2 s. Teste na Task 4.
4. `localStorage` indisponível (aba anônima, cota cheia): a app abre e funciona, só não guarda correções. Teste na Task 7.
5. Celular a 375 px: filas viram cartões, gráficos cabem, nada rola de lado. Teste Playwright na Task 10.

---

### Task 1: Exportar o modelo e as referências de paridade

**Files:**
- Create: `src/triagem/exportar_web.py`
- Test: `tests/test_exportar_web.py`
- Create (gerados): `web/public/modelo.json`, `web/tests/fixtures/paridade.json`

**Interfaces:**
- Produces:
  - `exportar_modelo(artefato: dict) -> dict` com chaves `classes` (lista de 8), `palavras` (`vocab: dict[str,int]`, `idf: list[float]`, `ngram: [1,2]`), `caracteres` (`vocab`, `idf`, `ngram: [3,5]`), `regras` (lista de `{nome, padrao}` na ordem de `REGRAS`), `coef` (8 × n_variáveis, arredondado a 6 casas), `intercepto` (8), `limiar` (float).
  - `prever_com_export(exp: dict, texto: str) -> dict` (`categoria`, `probas: dict[str,float]`): predição em Python puro a partir do export, a referência do algoritmo que o TypeScript copia.
  - `nunca_vistas() -> pd.DataFrame` (`review_id`, `texto`): pool menos os ids de `data/rotulos_claude.csv`.
  - CLI `python -m triagem.exportar_web` grava `web/public/modelo.json` e `web/tests/fixtures/paridade.json` (300 textos do teste via `dados.amostra_ouro`, sem rótulos, mais 1.000 de `nunca_vistas()` com `random_state=2026`; cada item `{texto, categoria, probas}` vindo do sklearn).

- [ ] **Step 1: Testes que falham**

```python
def test_export_tem_formato():
    exp = exportar_modelo(joblib.load(RAIZ / "results/modelo.joblib"))
    assert exp["classes"] == ROTULOS or sorted(exp["classes"]) == sorted(ROTULOS)
    n = len(exp["palavras"]["vocab"]) + len(exp["caracteres"]["vocab"]) + len(exp["regras"])
    assert len(exp["coef"]) == 8 and len(exp["coef"][0]) == n

def test_python_puro_igual_ao_sklearn():
    art = joblib.load(RAIZ / "results/modelo.joblib"); exp = exportar_modelo(art)
    textos = nunca_vistas().sample(300, random_state=1).texto.tolist() + ["", "😡😡", "123", "NÃO CHEGOU"]
    ref = probabilidades(art["modelo"], textos)
    for i, t in enumerate(textos):
        p = prever_com_export(exp, t)
        assert p["categoria"] == ref.iloc[i].idxmax()
        assert max(abs(p["probas"][c] - ref.iloc[i][c]) for c in ROTULOS) < 1e-3

def test_nunca_vistas_exclui_rotuladas():
    rot = set(pd.read_csv(RAIZ / "data/rotulos_claude.csv", dtype={"review_id": str}).review_id)
    nv = nunca_vistas()
    assert len(nv) == 7451 and not rot & set(nv.review_id)
```
- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_exportar_web.py -q` → FAIL (`ModuleNotFoundError`).
- [ ] **Step 3: Implementar.** `prever_com_export` segue exatamente o scikit-learn:
  - texto → `normalizar`;
  - palavras: tokens `re.findall(r"(?u)\b\w\w+\b", t)`, unigramas e bigramas (`" ".join`), só os do vocabulário;
  - caracteres (`char_wb`): para cada `w` em `t.split()`: `w = " " + w + " "`; para `n` de 3 a 5: anexar `w[0:n]`, depois avançar `offset` de 1 em 1 enquanto `offset + n < len(w)` anexando `w[offset:offset+n]`; se `offset == 0` após o laço de um `n`, parar (palavra curta conta uma vez);
  - cada bloco: contagem → `1 + log(tf)` → `× idf` → normalização L2 do bloco;
  - regras: 1 onde a regra dispara (`regras_que_disparam`), sem normalizar;
  - concatenar na ordem palavras, caracteres, regras → `coef · x + intercepto` → softmax.
- [ ] **Step 4:** mesmo comando → PASS; rodar `PYTHONPATH=src .venv/bin/python -m triagem.exportar_web` e conferir os dois arquivos.
- [ ] **Step 5: Commit** — `git switch -c ferramenta`; `git add src/triagem/exportar_web.py tests/test_exportar_web.py web/public/modelo.json web/tests/fixtures/paridade.json && git commit -m "Exporta o modelo e as referências de paridade para a web"`

---

### Task 2: Dados do painel

**Files:**
- Create: `src/triagem/painel.py`
- Test: `tests/test_painel.py`
- Create (gerado): `web/public/painel.json`

**Interfaces:**
- Consumes: `exportar_web.nunca_vistas` (Task 1), `results/triagem.csv` (predições do Python), `regras.regras_que_disparam`, `regras.REGRAS`.
- Produces:
  - `montar_painel(tri: pd.DataFrame, datas: pd.Series) -> dict` com:
    - `total` (int), `sem_humano` (int, `revisao == False`), `por_categoria` (`{cat: int}`), `por_mes` (`[{mes: "AAAA-MM", cat: int, ...}]`), `regras_top` (`{cat: [{nome, rotulo_legivel, n}]}` até 5 por categoria, só regras da própria categoria), `mensagens` (`[{id, texto, categoria, certeza, revisao, motivo, palavras, data}]`).
  - `ROTULO_LEGIVEL: dict[str, str]` com um texto curto por regra (ex.: `"nao_recebi": "Não recebi"`), cobrindo as 44.
  - CLI `python -m triagem.painel` grava `web/public/painel.json` a partir de `results/triagem.csv` filtrado por `nunca_vistas()` e `review_creation_date` de `data/raw/olist_order_reviews_dataset.csv`.

- [ ] **Step 1: Testes que falham**

```python
def tri_falso():
    return pd.DataFrame({"review_id": ["a", "b", "c"], "texto": ["não recebi", "veio quebrado", "xyz"],
                         "categoria": ["nao_recebido_atraso", "defeito_qualidade", "outro"],
                         "certeza": [0.9, 0.95, 0.4], "revisao": [False, False, True],
                         "motivo_revisao": ["", "", "certeza baixa"], "palavras": ["recebi", "quebrado", ""]})

def test_montar_painel_conta():
    p = montar_painel(tri_falso(), pd.Series(["2018-01-05", "2018-01-20", "2018-02-01"], index=["a", "b", "c"]))
    assert p["total"] == 3 and p["sem_humano"] == 2
    assert p["por_mes"][0]["mes"] == "2018-01" and p["por_mes"][0]["nao_recebido_atraso"] == 1
    assert p["regras_top"]["nao_recebido_atraso"][0]["nome"] == "nao_recebi"

def test_rotulo_legivel_cobre_todas_as_regras():
    assert {r.nome for r in REGRAS} == set(ROTULO_LEGIVEL)

def test_painel_real_so_nunca_vistas():
    import json
    p = json.loads((RAIZ / "web/public/painel.json").read_text())
    assert p["total"] == 7451
```
- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_painel.py -q` → FAIL.
- [ ] **Step 3: Implementar** `montar_painel`, `ROTULO_LEGIVEL` e a CLI; rodar a CLI.
- [ ] **Step 4:** mesmo comando → PASS.
- [ ] **Step 5: Commit** — `git add src/triagem/painel.py tests/test_painel.py web/public/painel.json && git commit -m "Gera os dados do painel com as reclamações nunca vistas pelo modelo"`

---

### Task 3: Esqueleto da app web

**Files:**
- Create: `web/package.json`, `web/next.config.ts` (`output: 'export'`), `web/tsconfig.json`, `web/vitest.config.ts`, `web/src/app/layout.tsx`, `web/src/app/page.tsx`
- Modify: `.gitignore` (`web/node_modules/`, `web/out/`, `web/.next/`), `.github/workflows/testes.yml` (job `web`: `npm ci && npm test && npm run build` em `web/`)

- [ ] **Step 1:** consultar o Context7 para Next.js 16 (App Router, `output: 'export'`) e Vitest 5 com TypeScript.
- [ ] **Step 2:** criar o projeto (`create-next-app` com TypeScript, App Router, sem Tailwind se a direção visual da Task 5 não pedir; ESLint), adicionar Vitest. Um teste `web/tests/smoke.test.ts` que importa `web/public/modelo.json` e confere 8 classes.
- [ ] **Step 3:** `cd web && npm test && npm run build` → teste passa e `web/out/index.html` existe.
- [ ] **Step 4: Commit** — `git add web .gitignore .github && git commit -m "Cria o esqueleto da app web com exportação estática"`

---

### Task 4: Modelo no navegador (TypeScript) com paridade

**Files:**
- Create: `web/src/modelo/normalizar.ts`, `web/src/modelo/regras.ts`, `web/src/modelo/tfidf.ts`, `web/src/modelo/prever.ts`, `web/src/modelo/tipos.ts`
- Test: `web/tests/paridade.test.ts`, `web/tests/prever.test.ts`

**Interfaces:**
- Consumes: `modelo.json` (Task 1), `paridade.json`.
- Produces:
  - `normalizar(texto: string): string` (igual a `src/triagem/normalizar.py`).
  - `regrasQueDisparam(textoNormalizado: string, regras: Regra[]): string[]`.
  - `prever(modelo: Modelo, texto: string): Predicao` com `categoria`, `probas: Record<string, number>`, `certeza`, `revisao: boolean`, `motivo: "" | "certeza baixa" | "texto sem conteúdo"`, `palavras: string[]` (3 de maior contribuição positiva no bloco de palavras).
  - `preverEmLotes(modelo, textos: string[], aoProgredir: (feitos: number) => void): Promise<Predicao[]>` (lotes de 200, cedendo a vez ao navegador entre lotes).

- [ ] **Step 1: Testes que falham**

```ts
test("mesma categoria e probabilidades do Python em todas as referências", () => {
  for (const r of paridade) {
    const p = prever(modelo, r.texto);
    expect(p.categoria).toBe(r.categoria);
    for (const c of modelo.classes) expect(Math.abs(p.probas[c] - r.probas[c])).toBeLessThan(1e-3);
  }
});
test("texto sem letras vai para revisão", () => {
  for (const t of ["", "😡😡😡", "123456789012345"]) expect(prever(modelo, t).motivo).toBe("texto sem conteúdo");
});
test("1.000 mensagens em menos de 2 s", async () => {
  const t0 = performance.now(); await preverEmLotes(modelo, paridade.slice(0, 1000).map(r => r.texto), () => {});
  expect(performance.now() - t0).toBeLessThan(2000);
});
```
- [ ] **Step 2:** `cd web && npx vitest run tests/paridade.test.ts tests/prever.test.ts` → FAIL.
- [ ] **Step 3: Implementar** espelhando `prever_com_export` (Task 1). Cuidados: `\w` do Python com Unicode vira `[\p{L}\p{N}_]` com a flag `u`; contar caracteres com `Array.from` (pontos de código, não UTF-16); as regex das regras são convertidas do Python (`(?:...)`, `\b` e lookbehind funcionam no JS moderno; trocar `\w` como acima); `idf` e coeficientes vêm do JSON.
- [ ] **Step 4:** mesmo comando → PASS (100% das referências).
- [ ] **Step 5: Commit** — `git add web/src/modelo web/tests && git commit -m "Roda o modelo no navegador com paridade total com o Python"`

---

### Task 5: Direção visual e estrutura da app

**Files:**
- Create: `web/src/app/globals.css` (tokens de cor, tipo, espaço, claro e escuro), `web/src/componentes/` (navegação, cabeçalho de seção, cartão de número), `web/src/dados/` (`carregarPainel(): Promise<Painel>`, contexto com os dados ativos: os da Olist ou os do usuário)
- Create: `docs/direcao-visual.md`

- [ ] **Step 1:** invocar `ui-ux-pro-max` para estilo, paleta e fontes de uma ferramenta interna de atendimento, e `impeccable` para fixar a direção. Registrar em `docs/direcao-visual.md` (público: recrutador e time de atendimento; tom; paleta com contraste AA; fontes do Google Fonts; uma ideia visual marcante que fuja de template).
- [ ] **Step 2:** implementar tokens e a estrutura de navegação (Painel, Filas, Revisão, Triar as minhas, Sobre) com a fonte de dados ativa trocável. Teste `web/tests/dados.test.ts`: `carregarPainel` devolve `total === 7451`.
- [ ] **Step 3:** `cd web && npm test && npm run build` → verde.
- [ ] **Step 4: Commit** — `git commit -am "Define a direção visual e a estrutura da app"` (incluindo arquivos novos).

---

### Task 6: Painel

**Files:**
- Create: `web/src/app/page.tsx` (Painel), `web/src/componentes/painel/*`
- Test: `web/tests/painel.test.ts`

**Interfaces:**
- Produces: `calcularResumo(mensagens: MensagemTriada[], segundosPorMensagem: number): Resumo` com `total`, `semHumano`, `pctSemHumano`, `horasPoupadas = semHumano × segundos / 3600`.

- [ ] **Step 1: Teste que falha**

```ts
test("horas poupadas usam a premissa", () => {
  const r = calcularResumo([{ revisao: false }, { revisao: false }, { revisao: true }] as any, 30);
  expect(r.semHumano).toBe(2); expect(r.horasPoupadas).toBeCloseTo(60 / 3600);
});
```
- [ ] **Step 2:** rodar → FAIL. **Step 3:** implementar `calcularResumo` e a tela: números principais (com a premissa de 30 s editável e escrita junto do número), barras por categoria (clique abre a fila), evolução por mês, problemas que mais aparecem (`regras_top`) com exemplos. Consultar o Context7 se usar biblioteca de gráficos. **Step 4:** testes e build verdes.
- [ ] **Step 5: Commit** — `git commit -am "Adiciona o painel"`.

---

### Task 7: Filas e Revisão

**Files:**
- Create: `web/src/app/filas/page.tsx`, `web/src/app/revisao/page.tsx`, `web/src/dados/correcoes.ts`, `web/src/dados/exportar.ts`
- Test: `web/tests/correcoes.test.ts`, `web/tests/exportar.test.ts`

**Interfaces:**
- Produces:
  - `aplicarCorrecoes(msgs: MensagemTriada[], correcoes: Record<string, string>): MensagemTriada[]` (a categoria corrigida vence; `corrigida: true`).
  - `lerCorrecoes(): Record<string, string>` e `salvarCorrecao(id, categoria): void`, que nunca lançam (sem `localStorage` vira memória).
  - `paraCsv(msgs: MensagemTriada[]): string` com cabeçalho `id;texto;categoria;certeza;revisao;motivo` e aspas escapadas.

- [ ] **Step 1: Testes que falham**

```ts
test("correção vence a predição", () => {
  expect(aplicarCorrecoes([{ id: "a", categoria: "outro" }] as any, { a: "sem_estoque" })[0].categoria).toBe("sem_estoque");
});
test("sem localStorage não quebra", () => {
  vi.stubGlobal("localStorage", { getItem() { throw new Error(); }, setItem() { throw new Error(); } });
  expect(() => salvarCorrecao("a", "outro")).not.toThrow(); expect(lerCorrecoes()).toEqual({ a: "outro" });
});
test("csv escapa aspas e ponto e vírgula", () => {
  expect(paraCsv([{ id: "a", texto: 'disse "oi"; tchau', categoria: "outro", certeza: 0.5, revisao: true, motivo: "certeza baixa" }] as any))
    .toContain('"disse ""oi""; tchau"');
});
```
- [ ] **Step 2:** rodar → FAIL. **Step 3:** implementar as funções e as telas (lista por categoria com busca, certeza, porquê, mover de fila; Revisão com as de `revisao === true`; exportar CSV). Lista longa paginada ou virtualizada. **Step 4:** verde.
- [ ] **Step 5: Commit** — `git commit -am "Adiciona as filas, a revisão e a exportação"`.

---

### Task 8: Triar as minhas

**Files:**
- Create: `web/src/app/triar/page.tsx`, `web/src/dados/csv.ts`
- Test: `web/tests/csv.test.ts`

**Interfaces:**
- Produces: `lerCsv(conteudo: string): { colunas: string[]; linhas: Record<string, string>[] }` (detecta `;` ou `,`, remove BOM, aceita aspas com quebra de linha) e `colunaDeTexto(colunas: string[]): string | null` (prefere `texto`, `review_comment_message`, `mensagem`, `comentario`; senão `null` e a tela pede para escolher).

- [ ] **Step 1: Testes que falham**

```ts
test("csv do Excel brasileiro", () => {
  const r = lerCsv('﻿id;mensagem\n1;"não chegou;\nainda"\n2;veio quebrado');
  expect(r.colunas).toEqual(["id", "mensagem"]); expect(r.linhas[0].mensagem).toBe("não chegou;\nainda");
  expect(colunaDeTexto(r.colunas)).toBe("mensagem");
});
test("coluna desconhecida pede escolha", () => { expect(colunaDeTexto(["a", "b"])).toBeNull(); });
```
- [ ] **Step 2:** rodar → FAIL. **Step 3:** implementar e a tela (colar uma por linha ou soltar CSV; `preverEmLotes` com barra de progresso; ao terminar, a fonte de dados ativa vira a do usuário, com botão para voltar aos dados da Olist). **Step 4:** verde.
- [ ] **Step 5: Commit** — `git commit -am "Permite triar as próprias reclamações no navegador"`.

---

### Task 9: Sobre

**Files:**
- Create: `web/src/app/sobre/page.tsx`

- [ ] **Step 1:** texto curto e honesto, só com números de `README.md`/`DECISOES.md`: acurácia igual ao Qwen nas 53 (75,5%), F1 menor (50,7% contra 56,0%), menos de 1 ms contra cerca de 1 s, a calibração do guia (33% para 75%), o painel usa só mensagens nunca vistas, link do repositório, dados da Olist com licença CC BY-NC-SA 4.0. Sem travessões.
- [ ] **Step 2:** `cd web && npm run build` → verde; `grep -c "—" web/src/app/sobre/page.tsx` → 0.
- [ ] **Step 3: Commit** — `git commit -am "Adiciona a página Sobre"`.

---

### Task 10: Qualidade visual e testes de ponta a ponta

**Files:**
- Create: `web/e2e/fluxo.spec.ts`, `web/playwright.config.ts`
- Create: `docs/screenshots/` (desktop e celular)

- [ ] **Step 1:** teste Playwright do fluxo principal em 1440×900 e 375×812: abre o Painel e vê 7.451; clica numa categoria e cai na fila; move uma mensagem de fila; vai em Triar, cola 3 mensagens, vê o resultado; confere que `document.documentElement.scrollWidth <= innerWidth` em cada tela no celular.
- [ ] **Step 2:** rodar com `playwright-cli` contra `npx serve web/out`; salvar screenshots em `docs/screenshots/`.
- [ ] **Step 3:** `web-design-guidelines` na UI; corrigir o que for confirmado.
- [ ] **Step 4:** `/impeccable polish`; testes e build verdes de novo.
- [ ] **Step 5: Commit** — `git add web docs/screenshots && git commit -m "Testa o fluxo em desktop e celular e faz o polimento visual"`.

---

### Task 11: Deploy e documentação

**Files:**
- Modify: `README.md` (link da ferramenta, screenshot, seção curta), `CLAUDE.md` (local), `Makefile` (alvo `web`: exportar modelo e painel)

- [ ] **Step 1:** `make web` (roda `triagem.exportar_web` e `triagem.painel`) e confere que os JSON não mudaram.
- [ ] **Step 2:** deploy na Vercel com diretório raiz `web/`, build `npm run build`, saída `out`. Se a Vercel exigir ação do Mateus (login, ligar o repositório), parar e pedir.
- [ ] **Step 3:** abrir o link publicado com o navegador e repetir o fluxo principal.
- [ ] **Step 4:** README: link e screenshot no topo; sem travessões.
- [ ] **Step 5:** `/code-review` do branch; corrigir o que for confirmado.
- [ ] **Step 6: Commit** — `git commit -am "Publica a ferramenta e linka no README"`.
