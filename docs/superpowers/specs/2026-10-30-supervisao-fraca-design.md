# Triagem por supervisão fraca: regras legíveis + ML, sem LLM

Data: 2026-10-30 · Situação: aprovado pelo Mateus em 2026-10-30. A ferramenta (parte 3) fica para depois.

## Intenção

Hoje o projeto compara LLMs locais (Qwen 2.5 7B e Llama 3.2 3B) com um TF-IDF + SVM treinado com rótulos gerados pelo Qwen. O Mateus decidiu mirar a trilha AI Builder e quer que a triagem funcione **sem depender de LLM nenhuma**, nem para rotular o treino: um modelo de machine learning treinado aqui, local e de graça.

O caminho escolhido é o mesmo desenho do projeto Fila Viva (Hackatona PUCRS, equipe Armelin Tech, em `~/Documents/3_GitHub/Armelin_Tech`): **regras legíveis onde não há verdade, modelo onde ajuda, e o humano na dúvida**. Aqui isso vira **supervisão fraca (weak supervision)**: regras legíveis rotulam as reclamações, um modelo clássico aprende com esses rótulos e generaliza para o que as regras não pegam, e os casos contraditórios ou incertos vão para revisão humana.

Por que importa: regras podem ser lidas e contestadas por qualquer pessoa; a opinião de uma LLM não. O projeto passa a mostrar um sistema completo, explicável e de custo zero, em vez de só uma tabela comparando modelos.

## Decidido pelo Mateus

- Rótulos de treino vêm de **regras legíveis** (supervisão fraca), não de LLM.
- Um modelo de **machine learning clássico**, treinado no projeto, roda local e sem custo.
- Haver uma etapa de **normalização** do texto antes de rotular e treinar.
- Seguir o rigor do Fila Viva: validação, controle, humano no circuito, explicação, decisões documentadas.
- **Fora agora:** a ferramenta online (app em Streamlit e publicação). Pode voltar depois.
- **Sem conjunto de desenvolvimento rotulado à mão.** As regras são escritas e julgadas lendo amostras do pool de treino; a qualidade real só aparece na avaliação final no ouro. O `DECISOES.md` registra essa limitação.

## Objetivos

1. Regras legíveis por categoria que rotulam o pool de treino (~10.400 reclamações fora do ouro e do few-shot), com relatório de cobertura e conflitos.
2. Um modelo clássico treinado só com esses rótulos, com validação cruzada.
3. Uma decisão final por mensagem (categoria, certeza, se vai para revisão e por quê), gravada num CSV, como o `fila_priorizada.csv` do Fila Viva.
4. Explicação por mensagem: qual regra disparou e quais palavras mais pesaram para o modelo.
5. Avaliação honesta no conjunto ouro, com as 53 mensagens do Mateus como régua principal, comparando regras sozinhas, modelo e o sistema híbrido. Os resultados de LLM já gravados ficam como referência.
6. Um `DECISOES.md` no estilo do Fila Viva.

## Não-objetivos

- App, deploy, API ou interface (parte 3, adiada).
- Multirrótulo. Continua uma categoria principal por mensagem.
- Embeddings, transformers ou qualquer modelo pré-treinado grande.
- Rodar LLM em qualquer etapa nova. O código de LLM existente fica, mas sai do caminho principal.

## Anti-objetivos (falharia mesmo funcionando)

- **Ajustar regras, limiares ou hiperparâmetros olhando o `data/ouro.csv`.** O ouro só é lido na avaliação final. Regras são escritas lendo o pool de treino e o `data/fewshot.csv`.
- Esconder ou maquiar o resultado se o modelo não ganhar das regras sozinhas. Se perder, o README e o `DECISOES.md` dizem isso.
- Regras opacas (listas gigantes geradas automaticamente). Cada regra precisa ser curta, ter nome e ter exemplos nos testes.
- Qualquer dependência paga ou que exija internet para rodar.
- Alterar os 53 rótulos com `fonte == mateus`.

## Restrições

- Python 3.9+ (o `.venv` local usa 3.9; o CI usa 3.11). Só pandas, numpy, scikit-learn, matplotlib e joblib, que já estão no projeto.
- `make tudo` deve rodar sem Ollama, do zero, em poucos minutos.
- TDD na lógica de negócio (normalização, regras, combinação, decisão final, explicação). Testes não chamam rede nem Ollama.
- Textos do Mateus (README, DECISOES, commits): sem travessões e sem números inventados; todo número sai de código rodado.
- Dados da Olist: CC BY-NC-SA 4.0, já citados no README.

## Como funciona

### 1. Normalização (`src/triagem/normalizar.py`)
Uma função `normalizar(texto) -> str`, usada **igual** nas regras, no treino e na predição:
- minúsculas e sem acentos;
- links e e-mails viram um marcador; números (datas, pedidos, valores) viram um marcador;
- letras repetidas três ou mais vezes viram uma ("péssimooooo" → "pessimo", "muuuito" → "muito");
- espaços e quebras de linha colapsados.

Os filtros atuais de `dados.reclamacoes()` continuam (nota 1 ou 2, pelo menos 15 caracteres, sem duplicatas).

### 2. Regras legíveis (`src/triagem/regras.py`)
- Cada regra tem nome, categoria e um padrão (expressão regular sobre o texto normalizado). Ela dispara ou se abstém.
- Exemplos do tipo: "nao chegou", "ainda nao recebi", "atras", "veio faltando", "so veio um", "veio errado", "diferente do anuncio", "veio quebrado", "defeito", "estorno", "reembolso", "cobrado duas vezes", "nao responde".
- **Combinação:** se só uma categoria recebe votos, ela é o rótulo. Se várias recebem, vale a regra principal da taxonomia (o problema que originou a reclamação), aplicada como ordem de prioridade: `nao_recebido_atraso` > `item_faltando` > `produto_errado` > `defeito_qualidade` > `cobranca_cancelamento` > `atendimento_loja`. A mensagem fica marcada com **conflito** quando duas categorias de origem (as quatro primeiras) disparam juntas. `outro` só vem de regras próprias (por exemplo, elogio com nota baixa).
- Se nenhuma regra dispara, a mensagem fica **sem rótulo** e não entra no treino.
- Relatório (`results/regras.md`): cobertura de cada regra e de cada categoria, quantas sem rótulo e quantas com conflito, no pool de treino.

### 3. Modelo (`src/triagem/modelo.py`)
- TF-IDF (palavras e caracteres, como o `baseline.py` atual) + **regressão logística** com `class_weight="balanced"`, que dá probabilidades para a certeza.
- Treina só com as mensagens que as regras rotularam sem conflito.
- `C` escolhido por validação cruzada estratificada em 5 partes (`random_state=42`) no próprio conjunto rotulado pelas regras.
- **Cuidado assumido:** a validação cruzada mede concordância com as regras, não acerto real. O acerto real só aparece no ouro.
- Artefato salvo em `results/modelo.joblib` (no `.gitignore`, como o atual).

### 4. Decisão final e humano no circuito (`src/triagem/triagem.py`)
Regra fixada antes de olhar o ouro:
- Se uma regra disparou sem conflito, a categoria é a da regra.
- Se não disparou nenhuma, ou houve conflito, a categoria é a do modelo.
- **Vai para revisão** quando: regra e modelo discordam; houve conflito entre regras; ou a certeza do modelo ficou abaixo de um limiar.
- O limiar é escolhido com predições fora da amostra (out-of-fold) da validação cruzada, nunca no ouro.

Saída `results/triagem.csv`, uma linha por reclamação do pool inteiro: `review_id`, `texto`, `categoria`, `origem` (regra ou modelo), `regra` (nome da que decidiu, se houver), `certeza`, `revisao` (sim/não), `motivo_revisao`, `palavras` (as que mais pesaram).

### 5. Explicação
Para cada mensagem: o nome da regra que disparou e as três palavras (só do TF-IDF de palavras, para ser legível) com maior contribuição para a classe prevista (coeficiente × peso TF-IDF).

### 6. Verdade observada para atraso (opcional, não bloqueia)
A base completa da Olist tem `olist_orders_dataset.csv`, com datas de entrega prometida e real, e liga às avaliações pelo `order_id`. Se o arquivo estiver em `data/raw/`, a avaliação mostra, entre as mensagens classificadas como `nao_recebido_atraso`, quantas são de pedidos de fato atrasados ou não entregues, comparado com a taxa geral. É só conferência, não vira variável do modelo. O Mateus precisa baixar o arquivo do Kaggle (exige login); sem ele, essa seção é pulada.

### 7. Avaliação (`src/triagem/avaliar.py`, adaptado)
No ouro (300) e nas 53 do Mateus, lado a lado:
- **Regras sozinhas** (sem rótulo vira `outro`): o controle, como o "modelo só com tempo de fila" do Fila Viva;
- **Modelo sozinho**;
- **Sistema híbrido** (a decisão final da seção 4);
- **Referências já gravadas:** Qwen 2.5 7B zero-shot e o SVM treinado com rótulos do Qwen, lidos de `results/preds/`.

Métricas atuais (acurácia, F1 macro com IC 95% por bootstrap, F1 por categoria, latência) mais: cobertura das regras, taxa de revisão e F1 do híbrido só nas mensagens que **não** foram para revisão.

### 8. Documentação
- `DECISOES.md` (novo): a decisão central, por que não usar LLM para rotular, as regras e a prioridade, o modelo, o limiar, a fila de revisão, os resultados e as limitações.
- `README.md` reescrito em torno da supervisão fraca; os LLMs viram uma seção de comparação.
- `Makefile`: `make tudo` = testes + regras + treinar + triagem + avaliar, sem Ollama. Os alvos de LLM continuam, fora do `tudo`.

## Critério de sucesso

- `make tudo` roda do zero, sem Ollama, e gera `results/regras.md`, `results/triagem.csv` e `results/resultados.md`.
- Testes cobrindo normalização, cada regra (casos que disparam e que não disparam), combinação e conflito, decisão final, revisão e explicação.
- O resultado no ouro é relatado como saiu. A meta, sem garantia, é o híbrido ganhar das regras sozinhas no F1 macro e nas 53 do Mateus.

## Deixado para quem for construir

- O conjunto exato de regras e padrões, dentro dos limites acima.
- O valor do limiar de certeza, pelo critério da seção 4.
- Nomes internos de funções e a organização dos testes.
- O formato visual do `results/regras.md`.

## Escolhas feitas por Claude (para o Mateus conferir)

- Regressão logística em vez de SVM, por dar probabilidade para a certeza.
- A ordem de prioridade entre categorias da seção 2.
- Regra decide quando dispara; modelo cobre o resto (seção 4).
- `outro` tem a menor prioridade: só vira rótulo quando nenhuma outra categoria dispara.
- Quando uma regra decide, `certeza` é a probabilidade que o modelo dá para a categoria da regra (informativa). Uma decisão de regra só vai para revisão se o modelo discordar ou houver conflito; o limiar de certeza vale só quando o modelo decide.
- O limiar é o menor valor em que, nas predições fora da amostra, as decisões aceitas do modelo concordam com as regras em pelo menos 85%.
- `results/triagem.csv` cobre só o pool de treino (o ouro fica de fora) e usa predições fora da amostra (out-of-fold) nas linhas que entraram no treino, para não inflar concordância nem certeza. É a fila operacional, não entra na avaliação.
- As regras são escritas por Claude lendo o pool de treino e ficam legíveis no código para o Mateus revisar; o `DECISOES.md` diz quem fez o quê.
- O README é reescrito como projeto de portfólio, sem citar programa ou empresa. A seção "Próximos passos" do `CLAUDE.md` local é atualizada junto.
- Datas reais de entrega só como conferência, não como variável.
- O código de LLM fica no repositório, fora do `make tudo`, e os resultados de LLM viram referência.
