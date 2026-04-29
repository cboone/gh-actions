ACTIONLINT_VERSION := 1.7.12
ACTIONLINT := .local/bin/actionlint
YAMLLINT_VENV := .local/yamllint-venv
YAMLLINT_REQ := requirements/yamllint.txt

.PHONY: lint lint-yaml lint-md format format-check spell setup help install-actionlint install-yamllint

install-actionlint:
	@VERSION=$(ACTIONLINT_VERSION) INSTALL_DIR=$(dir $(ACTIONLINT)) ./scripts/install-actionlint

install-yamllint:
	@if [ ! -x "$(YAMLLINT_VENV)/bin/yamllint" ] || ! cmp -s "$(YAMLLINT_REQ)" "$(YAMLLINT_VENV)/.requirements"; then \
		uv venv "$(YAMLLINT_VENV)" --quiet && \
		uv pip install --python "$(YAMLLINT_VENV)/bin/python" --require-hashes -r "$(YAMLLINT_REQ)" --quiet && \
		cp "$(YAMLLINT_REQ)" "$(YAMLLINT_VENV)/.requirements"; \
	fi

setup: install-actionlint install-yamllint ## Install local tool dependencies

lint: install-actionlint ## Lint GitHub Actions workflows
	$(ACTIONLINT)

lint-yaml: install-yamllint ## Lint YAML files
	$(YAMLLINT_VENV)/bin/yamllint .

lint-md: ## Lint Markdown files
	npx markdownlint-cli2 "**/*.md"

format: ## Format with Prettier
	npx prettier --write .

format-check: ## Check formatting with Prettier
	npx prettier --check .

spell: ## Check spelling
	npx cspell .

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'
