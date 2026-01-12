.PHONY: help install dev lint format test clean ruler repo-init-commons

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	uv sync --frozen

dev: ## Install development dependencies
	uv sync --frozen --all-extras

lint: ## Run linter (ruff check)
	uv run ruff check src/ tests/

format: ## Format code (ruff format)
	uv run ruff format src/ tests/

format-check: ## Check code formatting without making changes
	uv run ruff format --check src/ tests/

test: ## Run all tests
	uv run pytest

test-unit: ## Run unit tests only
	uv run pytest tests/unit/ -v

test-integration: ## Run integration tests only
	uv run pytest tests/integration/ -v

test-coverage: ## Run tests with coverage report
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html

clean: ## Clean up cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ htmlcov/ .coverage

clean-all: clean ## Clean everything including virtual environment
	rm -rf .venv/

# --- Commons from .github ---
ruler: ## Generate AI rules from .ruler/
	npx --yes @intellectronica/ruler apply

repo-init-commons: ## Initialize/update configs and AI rules from .github
	@if [ -d "../.github" ]; then \
		../.github/scripts/sync-configs.sh . --force; \
		../.github/scripts/sync-ruler.sh . --force; \
		$(MAKE) ruler; \
	else \
		echo "Error: .github repo not found at ../.github"; \
		exit 1; \
	fi
# --- End Commons ---
