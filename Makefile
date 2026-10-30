# Tudo roda localmente, sem custo. Os modelos rodam no Ollama.
VENV := .venv
PY := $(VENV)/bin/python
export PYTHONPATH := src

GRANDE ?= qwen2.5:7b
PEQUENO ?= llama3.2:3b

.PHONY: instalar testes modelos llm prata baseline avaliar tudo

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

avaliar: instalar
	$(PY) -m triagem.avaliar

tudo: testes modelos llm prata baseline avaliar
