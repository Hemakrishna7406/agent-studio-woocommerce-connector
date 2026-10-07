.PHONY: help install dev test cov demo lint fmt typecheck run clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install runtime dependencies
	pip install -r requirements.txt

dev: ## Install dev dependencies
	pip install -r requirements-dev.txt

test: ## Run the test suite
	python -m pytest

cov: ## Run tests with coverage
	python -m pytest --cov=connector --cov=mcp_server --cov-report=term-missing

demo: ## Run the zero-setup offline end-to-end demo
	python demo/demo_offline.py

lint: ## Lint with ruff
	ruff check .

fmt: ## Format with ruff
	ruff format .

typecheck: ## Type-check with mypy
	mypy connector mcp_server

run: ## Run the MCP server (stdio)
	python -m mcp_server.server

clean: ## Remove caches
	find . -type d -name __pycache__ -prune -exec rm -rf {} + ; \
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov
