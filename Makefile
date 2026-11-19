ACTIONLINT_VERSION := 1.7.12
ACTIONLINT := .local/bin/actionlint
YAMLLINT_VENV := .local/yamllint-venv
YAMLLINT_REQ := requirements/yamllint.txt

NODE ?= node
UV ?= uv
SCRUT ?= scrut
AUDIT_CACHE ?= $(CURDIR)/.local/scrut-release-audit
AUDIT_OUTPUT ?= $(CURDIR)/.local/scrut-release-audit.json

SCRUT_ENV = \
	HELLO_BIN="$(CURDIR)/tests/fixtures/hello.py" \
	UV_PYTHON_PREFERENCE=only-system \
	SCRUT_BIN="$$(command -v "$(SCRUT)")" \
	NODE_BIN="$$(command -v "$(NODE)")" \
	ZIG_FORMAT_FIXTURE="$(CURDIR)/tests/fixtures/check-zig-format-paths.mjs" \
	ARG_BINDING_FIXTURE="$(CURDIR)/tests/fixtures/check-workflow-arg-binding.mjs" \
	NPM_PUBLISH_FIXTURE="$(CURDIR)/tests/fixtures/check-npm-publish.mjs"

.PHONY: lint lint-yaml lint-md format format-check spell setup help install-actionlint install-yamllint

install-actionlint:
	@VERSION=$(ACTIONLINT_VERSION) INSTALL_DIR=$(dir $(ACTIONLINT)) ./scripts/install-actionlint

install-yamllint:
	@if [ ! -x "$(YAMLLINT_VENV)/bin/yamllint" ] || [ ! -f "$(YAMLLINT_VENV)/.requirements" ] || ! cmp -s "$(YAMLLINT_REQ)" "$(YAMLLINT_VENV)/.requirements"; then \
		uv venv "$(YAMLLINT_VENV)" --clear --quiet && \
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

.PHONY: test test-all test-scrut test-python test-node test-network

test: test-scrut test-python test-node ## Run local tests without binary downloads

test-all: lint lint-yaml lint-md format-check spell test ## Run lint, formatting and local tests

test-scrut: test-setup-uv test-scrut-installation test-zig-format-paths test-workflow-arg-binding test-npm-publish ## Run Scrut suites

test-python: test-trufflehog-positive-control test-scrut-release-audit test-shell-discovery test-tool-version-reporting test-gitleaks-config-errors ## Run local Python checks

test-node: test-checkout-credentials test-gitleaks-base-config ## Run Node checks

test-network: test-rust-tool-installs audit-scrut-releases ## Download and audit release binaries (network required)

.PHONY: test-setup-uv
test-setup-uv:
	env $(SCRUT_ENV) "$(SCRUT)" test tests/scrut/setup-uv.md

.PHONY: test-scrut-installation
test-scrut-installation:
	env $(SCRUT_ENV) "$(SCRUT)" test tests/scrut/installation.md

.PHONY: test-zig-format-paths
test-zig-format-paths:
	env $(SCRUT_ENV) "$(SCRUT)" test tests/scrut/zig-format-paths.md

.PHONY: test-workflow-arg-binding
test-workflow-arg-binding:
	env $(SCRUT_ENV) "$(SCRUT)" test tests/scrut/workflow-arg-binding.md

.PHONY: test-npm-publish
test-npm-publish:
	env $(SCRUT_ENV) "$(SCRUT)" test tests/scrut/npm-publish.md

.PHONY: test-trufflehog-positive-control
test-trufflehog-positive-control:
	"$(UV)" run --script tests/trufflehog-positive-control.py

.PHONY: test-scrut-release-audit
test-scrut-release-audit:
	SCRUT_BIN="$$(command -v "$(SCRUT)")" "$(UV)" run tests/check-scrut-release-audit.py

.PHONY: test-shell-discovery
test-shell-discovery:
	"$(UV)" run tests/check-shell-discovery.py

.PHONY: test-tool-version-reporting
test-tool-version-reporting:
	"$(UV)" run --script tests/check-tool-version-reporting.py

.PHONY: test-gitleaks-config-errors
test-gitleaks-config-errors:
	"$(UV)" run --script tests/check-gitleaks-config-errors.py

.PHONY: test-rust-tool-installs
test-rust-tool-installs:
	"$(UV)" run tests/check-rust-tool-installs.py

.PHONY: test-checkout-credentials
test-checkout-credentials:
	"$(NODE)" tests/check-checkout-credentials.mjs

.PHONY: test-gitleaks-base-config
test-gitleaks-base-config:
	"$(NODE)" tests/check-gitleaks-base-config.mjs

.PHONY: audit-scrut-releases
audit-scrut-releases:
	"$(UV)" run tests/audit-scrut-releases.py --native-only --cache "$(AUDIT_CACHE)" --output "$(AUDIT_OUTPUT)"

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'
