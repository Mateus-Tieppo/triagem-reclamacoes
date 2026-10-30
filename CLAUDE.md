# Triagem de reclamações

Projeto de portfólio do Mateus para o Programa de Estágio GenAI do iFood (trilha AI Engineer).
Classifica reclamações de e-commerce em português (base pública da Olist) em 7 categorias e
compara LLMs locais (zero-shot e few-shot) com TF-IDF + SVM.

## Regras do projeto

- Tudo roda localmente e de graça, com Ollama. Não adicionar API paga nem SDK de provedor pago.
- Nos textos do Mateus (README, commits, perfil) não usar travessões e não inventar experiência ou números.
- O conjunto de teste (`data/ouro.csv`) nunca é usado para escolher prompt, exemplos ou hiperparâmetros.
- Os 53 rótulos com `fonte == mateus` são do Mateus e não devem ser alterados sem ele pedir.

## Comandos

- `make tudo`: testes, baixa os modelos, roda os experimentos e gera `results/resultados.md`
- `make testes`: 14 testes, sem chamar o Ollama
- `make avaliar`: refaz a tabela a partir de `results/preds/`

Os comandos usam um ambiente virtual em `.venv`, criado na primeira execução.
Modelos: `qwen2.5:7b` e `llama3.2:3b`. Troque com `make llm GRANDE=... PEQUENO=...`.

## Próximos passos

1. Rodar `make tudo` e colocar a tabela de `results/resultados.md` na seção Resultados do README.
2. Escrever a análise dos resultados (onde cada abordagem erra, custo de latência).
3. Publicar como repositório público em github.com/Mateus-Tieppo e fixar no perfil.
