random_link_collector = ${HOME}/workspace/random_link_collector
export PIPENV_VENV_IN_PROJECT:=1

files := $(shell git diff HEAD --diff-filter=d --name-only | grep "\.py$$" | xargs printf "../%s\n")

.PHONY: lint
lint:
	@if [ -z "$(files)" ]; then echo "No staged files detected."; exit 0; fi; \
	python -m pylint --version
	python -m pylint src

.PHONY: test
test:
	@if [ -z "$(files)" ]; then echo "No staged files detected."; exit 0; fi; \
	python -m pytest --version
	python -m pytest tests

.PHONY: black
black:
	@if [ -z "$(files)" ]; then echo "No staged files detected."; exit 0; fi; \
	black .

.PHONY: isort
isort:
	@if [ -z "$(files)" ]; then echo "No staged files detected."; exit 0; fi; \
	isort $(files) --profile black --line-length 120

.PHONY: mypy
mypy:
	@if [ -z "$(files)" ]; then echo "No staged files detected."; exit 0; fi; \
	mypy $(files) --ignore-missing-imports --follow-imports=skip --strict --allow-untyped-decorators

.PHONY: ci
	ci: lint black isort mypy

install:
	pipenv install

git_do:
	git add .; git commit -m $"{message}"; git push

run:
	pipenv run streamlit run src/Submit.py
