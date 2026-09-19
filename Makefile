.PHONY: install install-dev scan

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

# Scan a skill/tool directory or file for vulnerabilities before trusting it.
# Static analysis only (no LLM API key required). For the deeper semantic
# pass, unset --no-llm and configure an LLM provider key (see SkillSpector docs).
# Usage: make scan SKILL=./path/to/skill
scan:
ifndef SKILL
	$(error Usage: make scan SKILL=./path/to/skill)
endif
	skillspector scan $(SKILL) --no-llm
