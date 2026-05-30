.PHONY: help install lint format test test-fast test-integration clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

lint: ## Run linter
	uv run ruff check libs/ packages/

format: ## Format code
	uv run ruff format libs/ packages/

type-check: ## Run type checking
	uv run mypy libs/core/src/behavior_core --ignore-missing-imports

test: ## Run all tests
	uv run pytest tests/ -v

test-fast: ## Run fast tests (no external deps)
	uv run pytest tests/test_core/ tests/test_stream/ tests/test_rules/ -v

test-integration: ## Run integration tests
	TEST_REAL_DEPS=1 uv run pytest tests/test_integration/ -v

test-coverage: ## Run tests with coverage
	uv run pytest tests/ --cov=libs --cov=packages --cov-report=html -v

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

docker-up: ## Start Docker services
	docker-compose -f infrastructure/docker/docker-compose.yml up -d

docker-down: ## Stop Docker services
	docker-compose -f infrastructure/docker/docker-compose.yml down

docker-logs: ## View Docker logs
	docker-compose -f infrastructure/docker/docker-compose.yml logs -f

mock-start: ## Start mock service
	uv run uvicorn behavior_mock.main:app --port 8001 --reload

rules-start: ## Start rules service
	uv run uvicorn behavior_rules.main:app --port 8002 --reload

insight-start: ## Start insight service
	uv run uvicorn behavior_insight.main:app --port 8003 --reload

audit-start: ## Start audit service
	uv run uvicorn behavior_audit.main:app --port 8004 --reload

logs-start: ## Start logs service
	uv run uvicorn behavior_logs.main:app --port 8005 --reload

generate-events: ## Generate test events
	curl -X POST http://localhost:8001/api/agent-mock/generate \
		-H "Content-Type: application/json" \
		-d '{"count": 100, "agent_type": "llm_agent"}'

check-health: ## Check service health
	@echo "Mock:" && curl -s http://localhost:8001/health | python -m json.tool
	@echo "Rules:" && curl -s http://localhost:8002/health | python -m json.tool
	@echo "Insight:" && curl -s http://localhost:8003/health | python -m json.tool
