.PHONY: help check test clean

# Default action when running bare 'make'
help:
	@echo "🤖 Pendula Pipeline Commands:"
	@echo "  make check      Run ultra-fast static testing pipeline (ruff, bandit, vulture, etc.)"
	@echo "  make test       Run static checks followed immediately by pytest"
	@echo "  make clean      Wipe out cache tracking footprints"

# 1. The "Check" Target: Aggregates all quick static testing tools via uv run
check:
	@echo "🔍 Invoking static analysis suite..."
	@echo "⚡ [1/5] Ruff (Lint & Style)..."
	uv run ruff check src/ --fix
	uv run ruff format src/ --check
	
	@echo "🦺 [2/5] Bandit (Security Audit)..."
	uv run bandit -c pyproject.toml -r src/
	
	@echo "🦤 [3/5] Vulture (Dead Code Finder)..."
	uv run vulture src/ --min-confidence 80
	
	@echo "🧼 [4/5] Refurb (Code Modernization)..."
	uv run refurb src/
	
	@echo "📝 [5/5] Interrogate (Docstring Coverage)..."
	uv run interrogate src/
	@echo "✅ All static validation matrices passed."

# 2. The "Test" Target: The master gate command that runs absolutely everything
test: check
	@echo "🚀 Launching pytest execution engine..."
	uv run pytest -v --durations=5

# Clean framework workspace caching folders
clean:
	@echo "🧹 Clearing artifact caches..."
	rm -rf .pytest_cache .ruff_cache .mypy_cache .vulture_cache .uv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

