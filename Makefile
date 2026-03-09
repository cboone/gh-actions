ACTIONLINT_VERSION := 1.7.11
YAMLLINT_VERSION := 1.37.1
ACTIONLINT := .local/bin/actionlint

.PHONY: lint lint-yaml lint-md format format-check spell setup help

$(ACTIONLINT):
	@VERSION=$(ACTIONLINT_VERSION) INSTALL_DIR=.local/bin ./scripts/install-actionlint

setup: $(ACTIONLINT) ## Install local tool dependencies

lint: $(ACTIONLINT) ## Lint GitHub Actions workflows
	$(ACTIONLINT)

lint-yaml: ## Lint YAML files
	uv tool run --from "yamllint==$(YAMLLINT_VERSION)" yamllint .

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
