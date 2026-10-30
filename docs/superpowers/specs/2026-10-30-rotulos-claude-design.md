# Melhorar o modelo com rótulos do Claude no treino

Data: 2026-10-30 · Situação: aprovado pelo Mateus em 2026-10-30

## Intenção

O sistema atual (supervisão fraca: regras legíveis + regressão logística) tem 54,9% de F1 macro no conjunto ouro e 44,9% nas 53 mensagens rotuladas pelo Mateus. O Qwen 2.5 7B zero-shot faz 74,9% e 60,5%. O Mateus quer superar o Qwen continuando com **ML clássico, local e de graça na ferramenta final**.

O gargalo é a qualidade dos rótulos de treino: o modelo copia os erros das regras. A mudança é trocar a fonte dos rótulos: **o Claude rotula uma única vez uma parte do pool de treino**, com as mesmas regras de rotulagem usadas no ouro, e o modelo clássico aprende com isso. As regras deixam de decidir e viram pistas (variáveis) para o modelo.

## Decidido pelo Mateus

- Só ML clássico na ferramenta. **Nada de embeddings, transformers ou LLM rodando na triagem.**
- **O Claude rotula o treino, uma única vez, durante o desenvolvimento.** O Mateus aceitou que, com isso, o projeto deixa de dizer "sem LLM nenhuma": README e `DECISOES.md` passam a dizer que os rótulos de treino vieram do Claude.
- Seguir a proposta: cerca de 3.000 mensagens rotuladas, parte sorteada como conjunto de desenvolvimento, parte escolhida pelo modelo atual; regras como pistas; régua principal nas 53 do Mateus; teste rodado uma vez no fim.

## Objetivos

1. Um conjunto de desenvolvimento de **500 mensagens sorteadas** do pool de treino, rotuladas pelo Claude, usado para todas as escolhas (modelo, hiperparâmetros, forma de treino, limiar).
2. **2.500 mensagens de treino** rotuladas pelo Claude: 1.000 sorteadas e 1.500 escolhidas pelo modelo atual entre as mais incertas.
3. Uma medida da consistência do Claude: 200 mensagens do desenvolvimento rotuladas de novo, às cegas, por outro agente; concordância e kappa relatados.
4. Comparar no desenvolvimento algumas combinações de modelo e forma de treino e ficar com a melhor por F1 macro.
5. Avaliar no ouro uma vez, com a régua principal nas 53 do Mateus, e relatar como sair.
6. Atualizar README, `DECISOES.md` e `results/resultados.md`.

## Não-objetivos

- Embeddings, BERT, SetFit ou qualquer modelo pré-treinado.
- A ferramenta para usar a triagem (continua adiada).
- Multirrótulo.
- Rotulagem iterativa em várias rodadas (uma rodada só).

## Anti-objetivos

- **O ouro ou os rótulos do Mateus chegarem aos agentes que rotulam.** Os agentes só recebem textos do pool de treino e as regras da taxonomia. Não podem ler `data/ouro.csv`, `rotulagem/` nem `results/`.
- Escolher qualquer coisa olhando o ouro. O ouro só é lido em `avaliar.py`, na avaliação final.
- Apresentar o F1 nas 300 do ouro como prova de que passou do Qwen. Como 247 delas também foram rotuladas pelo Claude, essa comparação favorece o modelo novo; a comparação honesta é nas 53.
- Esconder o resultado se não passar do Qwen.
- Alterar os 53 rótulos do Mateus.

## Restrições

- Python 3.9+, pandas, numpy, scikit-learn, matplotlib, joblib. Nenhuma dependência nova.
- `make tudo` continua rodando sem Ollama e sem chamar o Claude: os rótulos do Claude ficam salvos num CSV versionado, e o pipeline só lê esse arquivo.
- TDD na lógica de negócio (seleção da amostra, junção de rótulos, variáveis das regras, escolha do modelo, limiar).
- Textos do Mateus sem travessões e sem números inventados.
- O custo da rotulagem é uso de tokens do Claude na assinatura do Mateus, uma vez. A ferramenta final continua com custo zero.

## Como funciona

### 1. Seleção (`src/triagem/selecao.py`)
- Desenvolvimento: 500 mensagens sorteadas do `dados.pool_de_treino()` com `random_state=42`.
- Treino aleatório: 1.000 sorteadas do restante.
- Treino incerto: 1.500 do restante com menor certeza no modelo atual (`results/modelo.joblib`, maior probabilidade mais baixa).
- Os três grupos não se sobrepõem. Saída: `data/para_rotular.csv` com `review_id`, `texto`, `grupo` (`dev`, `aleatorio`, `incerto`).

### 2. Rotulagem pelo Claude
- O arquivo é dividido em lotes de cerca de 150 mensagens, embaralhados (os agentes não sabem de qual grupo vem cada mensagem). Cada lote vai para um agente novo, que recebe só os textos do lote e o guia de rotulagem (`taxonomia.py`), e devolve `review_id`, `rotulo`, `duvida` (verdadeiro quando ficou entre duas categorias).
- Os lotes são juntados em `data/rotulos_claude.csv` (`review_id`, `rotulo`, `duvida`, `grupo`), versionado no repositório.
- Checagem de formato: todo `review_id` do arquivo de entrada tem exatamente um rótulo válido.
- Consistência: 200 mensagens do grupo `dev`, sorteadas, são rotuladas de novo por outros agentes, sem ver os primeiros rótulos. Concordância e kappa vão para o `DECISOES.md`. Os rótulos usados continuam sendo os da primeira passada.

### 3. Variáveis das regras
As 43 regras viram 43 colunas 0/1 (disparou ou não), somadas às variáveis TF-IDF. Isso deixa o modelo usar o que as regras sabem sem obedecer a elas.

### 4. Modelos comparados no desenvolvimento
Todos com TF-IDF de palavras (1 e 2) e caracteres (3 a 5) mais as variáveis das regras:
- regressão logística (`class_weight="balanced"`);
- SVM linear calibrado (para ter probabilidade);
- Naive Bayes complementar.

Formas de treino:
- A: só os 2.500 rótulos do Claude;
- B: rótulos do Claude mais os rótulos das regras no resto do pool (sem conflito), com peso 0,1 e 0,3.

Hiperparâmetros por validação cruzada dentro do treino; a escolha final entre modelo e forma de treino é pelo F1 macro no desenvolvimento. Todas as combinações e seus F1 no desenvolvimento vão para `results/desenvolvimento.md`.

### 5. Decisão final e revisão
- O modelo escolhido decide sempre. As regras não têm mais a palavra final.
- Vai para revisão quando a certeza fica abaixo do limiar ou o texto não tem letras.
- O limiar usa o critério atual por faixas (`escolher_limiar`, alvo 85%), agora calculado no desenvolvimento, contra os rótulos do Claude.

### 6. Avaliação
Tabela no ouro com o modelo novo ao lado das referências já existentes (Qwen, Llama, SVM com rótulos do Qwen, supervisão fraca atual). Colunas atuais, mais uma linha de aviso sobre os 247 rótulos do Claude no ouro. O F1 no desenvolvimento do modelo escolhido também aparece, para mostrar quanto ele cai do desenvolvimento para o teste.

### 7. Documentação
- `DECISOES.md`: nova seção sobre os rótulos do Claude (por que, como, consistência, o viés no ouro), seção 2 reescrita, resultados novos. A supervisão fraca vira histórico.
- README: abertura e resultados atualizados; deixa de dizer "sem LLM" e passa a dizer "sem LLM na triagem; rótulos de treino feitos uma vez pelo Claude".

## Critério de sucesso

- `make tudo` roda sem Ollama e sem chamar o Claude.
- Testes cobrindo seleção, junção e checagem dos rótulos, variáveis das regras, escolha pelo desenvolvimento e decisão final.
- Resultado relatado como sair. A meta, sem garantia, é passar dos 60,5% do Qwen nas 53 do Mateus.

## Deixado para quem for construir

- Nomes de funções, organização dos testes e formato de `results/desenvolvimento.md`.
- A grade de hiperparâmetros de cada modelo.
- O texto exato das instruções aos agentes, desde que contenha só os textos do lote e as definições da taxonomia.

## Escolhas feitas por Claude (para o Mateus conferir)

- 500 de desenvolvimento, 1.000 sorteadas e 1.500 incertas.
- Lotes de cerca de 150 mensagens por agente.
- Checar consistência com 200 mensagens rotuladas duas vezes.
- Regras como 43 colunas 0/1, e não como decisão.
- Os três modelos e as duas formas de treino da seção 4.
- O modelo decide sempre; a revisão vem só da certeza e de texto vazio.
- A supervisão fraca atual fica no repositório como referência, não é apagada.
- **Guia dos agentes:** as definições e o `REGRAS` de `taxonomia.py` mais o bloco "Regras de rotulagem" de `rotulagem/template.html` (o mesmo guia usado no ouro), copiado para `taxonomia.py` como `GUIA_ROTULAGEM` antes de rotular. Os agentes não recebem nenhum rótulo, só o guia e os textos.
- **Desenvolvimento limpo:** o sorteio do desenvolvimento exclui as mensagens lidas para escrever as regras (`amostra_desenvolvimento(200, seed)` para as sementes 0 a 3) e usa outra semente (`random_state=2026`).
- **Estrutura:** `selecao.py` roda uma vez, fora do `make tudo`; `data/para_rotular.csv` guarda a certeza do modelo atual usada na escolha, então a seleção fica reproduzível sem depender do `modelo.joblib`. A supervisão fraca continua no `make tudo` como referência, gravando `results/supervisao_fraca/` (modelo, fila e relatório); o modelo novo passa a gravar `results/modelo.joblib` e `results/triagem.csv`.
- **Quem rotula:** o próprio Claude, durante a execução do plano, lançando os agentes (cerca de 17 lotes, mais 2 da checagem de consistência), no modelo padrão da sessão. O `DECISOES.md` registra o modelo usado e que os 247 rótulos do ouro vieram de uma sessão anterior do Claude.
- **Modelo final:** treinado só com os 2.500 de treino (mais os rótulos das regras, se a forma B vencer). O desenvolvimento não entra no treino final, para que o limiar e a comparação desenvolvimento contra teste continuem honestos.
