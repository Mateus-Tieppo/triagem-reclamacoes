# Tudo roda localmente, sem custo. O `make tudo` não usa LLM; os alvos de LLM (modelos, llm, prata, baseline) ficam só para a comparação.
VENV := .venv
PY := $(VENV)/bin/python
export PYTHONPATH := src

GRANDE ?= qwen2.5:7b
PEQUENO ?= llama3.2:3b

.PHONY: instalar testes modelos llm prata baseline regras supervisao selecionar treinar avaliar web tudo

$(PY):
	python3 -m venv $(VENV)
	$(PY) -m pip install -q --upgrade pip

instalar: $(PY)
	$(PY) -m pip install -q -e ".[dev]"

testes: instalar
	$(PY) -m pytest -q

modelos:
	ollama pull $(GRANDE)
	ollama pull $(PEQUENO)

llm: instalar
	$(PY) -m triagem.rodar_llm --modelo $(PEQUENO) --modo zero
	$(PY) -m triagem.rodar_llm --modelo $(PEQUENO) --modo few
	$(PY) -m triagem.rodar_llm --modelo $(GRANDE) --modo zero
	$(PY) -m triagem.rodar_llm --modelo $(GRANDE) --modo few

prata: instalar
	$(PY) -m triagem.rodar_llm --modelo $(GRANDE) --modo few --conjunto prata --n 2000

baseline: instalar
	$(PY) -m triagem.baseline --prata results/preds/prata__ollama__$(subst :,-,$(GRANDE))__few.jsonl

regras: instalar
	$(PY) -m triagem.regras

supervisao: instalar
	$(PY) -m triagem.triagem

selecionar: instalar
	$(PY) -m triagem.selecao

treinar: instalar
	$(PY) -m triagem.desenvolvimento

avaliar: instalar
	$(PY) -m triagem.avaliar

tudo: testes regras supervisao treinar avaliar

# Exporta o modelo e o painel para a ferramenta em web/ e roda os testes dela.
web: instalar
	$(PY) -m triagem.exportar_web
	$(PY) -m triagem.painel
	cd web && npm ci && npm test && npm run build
