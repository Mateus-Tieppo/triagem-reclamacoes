# Central de triagem: ferramenta web para o modelo

Data: 2026-10-31 · Situação: aprovado pelo Mateus em 2026-10-31

## Intenção

O modelo já empata com o Qwen 2.5 7B em acurácia nas mensagens rotuladas pelo Mateus, mas hoje só existe como experimento (CSV e tabelas). Para a trilha AI Builder, o que pesa é algo que um recrutador abre, usa e entende em segundos. A ferramenta transforma o modelo numa **central de triagem com painel**: um produto que parece interno de um time de atendimento, bonito e fácil, e que mostra a dor que resolve.

## Decidido pelo Mateus

- Mistura de **ferramenta interna** (filas por time, revisão, exportação) com **dashboard** (visão das 10 mil reclamações).
- O recrutador precisa **se impressionar ao bater o olho**, achar **útil e fácil**, ver **capricho no visual** e ver que **resolve uma dor real**, conseguindo **usar rápido**.
- **Deploy** gratuito. Supabase só se agregar valor (decisão abaixo: fica para uma v2).
- Seguir as escolhas propostas: Next.js com exportação estática na Vercel, visual com a skill impeccable, modelo no navegador com teste de paridade contra o Python, painel pré-calculado, documento de design e plano antes do código.

## Objetivos

1. **Abre já funcionando:** carregada com as 10.451 reclamações reais do pool, triadas pelo modelo. Nada para subir antes de ver valor.
2. **Painel:** números principais (triadas, resolvidas sem humano, tempo de leitura poupado com premissa explícita, tempo por mensagem), distribuição por categoria, evolução por mês (datas reais da base) e problemas que mais aparecem, com exemplos reais e as palavras que pesaram.
3. **Filas:** uma por categoria, como num sistema de atendimento. Cada reclamação mostra categoria, certeza e o porquê (palavras e regras). O usuário pode mover para outra fila. Exporta CSV.
4. **Revisão:** fila separada com as mensagens de certeza baixa ou sem texto, como no pipeline.
5. **Triar as próprias reclamações:** colar mensagens (uma por linha) ou subir um CSV; o painel e as filas passam a mostrar esses dados, triados no próprio navegador.
6. **Sobre o projeto:** uma seção curta e honesta com os resultados (acurácia igual ao Qwen nas 53, F1 menor, mil vezes mais rápido), a calibração do guia e o link do repositório.
7. **Mesma resposta do Python:** o modelo no navegador dá a mesma categoria que o Python em todas as mensagens do teste e de uma amostra do pool.

## Não-objetivos (v1)

- Backend, banco de dados, login. Supabase fica para uma v2 (correções da revisão virando dados de treino, com login e RLS).
- Retreinar o modelo no navegador.
- LLM em qualquer parte da ferramenta.
- Multirrótulo na interface (a secundária existe nos dados de treino, mas o modelo prevê só a principal).

## Anti-objetivos

- **Cara de template de IA** (gradiente roxo genérico, cards iguais, ícones aleatórios). O visual precisa de direção clara e capricho.
- **Números inventados.** Todo número na tela sai dos dados ou de uma premissa escrita na própria tela.
- **Mandar dados do usuário para fora.** O que ele cola ou sobe fica no navegador.
- **Resultado diferente do medido:** se o navegador divergir do Python, a ferramenta mostraria outro modelo.
- Esconder as limitações (F1 menor que o Qwen, teste humano pequeno).

## Restrições

- Custo zero: Vercel gratuita, sem API paga, sem servidor.
- Funcionar bem no celular (o recrutador pode abrir pelo LinkedIn no telefone).
- Acessibilidade: contraste, foco visível, teclado, `prefers-reduced-motion`.
- Fluxo do Mateus: impeccable e ui-ux-pro-max para o visual, vercel-react-best-practices e composition-patterns no React, GSAP com `useGSAP` se houver animação, Playwright para testar em desktop e mobile, web-design-guidelines na revisão de UI, TDD na lógica (modelo no navegador, cálculos do painel, leitura de CSV).
- Textos do Mateus sem travessões.

## Como funciona

### Exportação do modelo (Python)
Um script exporta `results/modelo.joblib` para JSON: vocabulário e idf dos dois TF-IDF (palavras 1 a 2, caracteres 3 a 5 com `char_wb`), configurações (`sublinear_tf`, normalização L2 por bloco), coeficientes e interceptos da regressão logística (8 categorias × 23.610 variáveis), limiar de certeza. As 44 regras vão como lista de padrões. O modelo tem cerca de 190 mil números; o JSON deve ficar em poucos MB e ser comprimido no deploy.

### Modelo no navegador (TypeScript)
Reimplementa: `normalizar`, tokenização igual à do scikit-learn (padrão `\b\w\w+\b` para palavras; `char_wb` com espaços em volta de cada palavra), TF-IDF com `sublinear_tf` e L2 por bloco, as regras como variáveis 0/1, produto com os coeficientes, softmax, limiar e o motivo de revisão (certeza baixa ou texto sem letras). Explicação: as palavras com maior contribuição, como no Python.

### Teste de paridade
O Python grava, para as 300 mensagens do teste e uma amostra de 1.000 do pool, a categoria e as probabilidades. O teste do TypeScript exige a mesma categoria em 100% e probabilidades iguais até a terceira casa.

### Dados do painel (Python)
Um script gera JSON a partir de `results/triagem.csv` mais as datas de `review_creation_date` da base: contagens por categoria, por mês, por fila, revisão, exemplos com palavras, e o texto de cada reclamação para as filas.

### Interface (Next.js, exportação estática)
Seções: Painel, Filas, Revisão, Triar as minhas, Sobre. Correções (mover de fila) ficam no `localStorage` do navegador. Exportar gera CSV no navegador.

### Deploy
Vercel, projeto conectado ao repositório, build estático. Link no README e no perfil do GitHub.

## Critério de sucesso

- Link público funcionando, sem custo.
- Teste de paridade passando.
- Fluxo principal testado com Playwright em desktop e celular, com screenshots.
- Revisão com web-design-guidelines sem problemas de acessibilidade.

## Deixado para quem for construir

- A direção visual detalhada (definida com impeccable e ui-ux-pro-max no início da construção).
- Biblioteca de gráficos, organização de componentes, nomes.
- Como paginar ou virtualizar as filas com 10 mil itens.

## Escolhas feitas por Claude (para o Mateus conferir)

- Supabase fica para uma v2; na v1, correções no `localStorage`.
- **Tempo de leitura poupado:** premissa padrão de 30 segundos por mensagem para ler e encaminhar, escrita na tela e ajustável pelo usuário. O número é apresentado como estimativa, não como medição.
- O código da ferramenta fica numa pasta `web/` dentro do mesmo repositório.
- **O painel mostra só as mensagens que o modelo nunca viu:** as 10.451 do pool menos as 3.000 rotuladas pelo Claude (treino e desenvolvimento), ou seja, 7.451 reclamações. Assim "resolvidas sem humano" fica honesto (cerca de 76%, como no DECISOES) e o modelo no navegador dá a mesma resposta que o painel. A amostra do teste de paridade sai desse mesmo conjunto. O conjunto de teste (300) não entra no painel.
- **"Problemas que mais aparecem"** são as regras legíveis (por exemplo "não recebi", "só veio um", "veio quebrado", "estorno"): o script de dados calcula quais regras disparam em cada mensagem e conta. É legível para um recrutador e mostra os subproblemas dentro de cada categoria.
- **Arquivos versionados:** o JSON do modelo exportado, os dados do painel e as referências do teste de paridade ficam em `web/` (versionados), para o build e o CI funcionarem sem o `joblib`.
- **Repositório e deploy:** o repositório já é público. O deploy na Vercel usa a conta do Mateus (ele aprovou o deploy); se alguma etapa exigir ação dele no painel da Vercel, o plano para e pede.
- **Enquadramento:** trilha AI Builder. Os textos da ferramenta e do README não citam programa nem empresa.
