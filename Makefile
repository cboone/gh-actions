.PHONY: lint lint-yaml lint-md format format-check spell help

lint: ## Lint GitHub Actions workflows
	actionlint

lint-yaml: ## Lint YAML files
	yamllint .

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
