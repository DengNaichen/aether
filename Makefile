.PHONY: help up down restart logs shell test clean build

# Default target - show help
help:
	@echo "Aether Learning Platform - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Setup:"
	@echo "  setup        - First time setup (copy .env.example to .env.local)"
	@echo ""
	@echo "Development:"
	@echo "  up           - Start all services"
	@echo "  down         - Stop all services"
	@echo "  restart      - Restart all services"
	@echo "  build        - Rebuild Docker images"
	@echo "  logs         - View logs from all services"
	@echo "  logs-web     - View web server logs only"
	@echo "  logs-worker  - View worker logs only"
	@echo ""
	@echo "Database:"
	@echo "  init-data    - Initialize development data (course + knowledge graph)"
	@echo "  db-shell     - Open PostgreSQL shell"
	@echo "  redis-shell  - Open Redis CLI"
	@echo ""
	@echo "Testing:"
	@echo "  test         - Run all tests"
	@echo "  test-v       - Run tests (verbose)"
	@echo "  test-cov     - Run tests with coverage report"
	@echo ""
	@echo "Utilities:"
	@echo "  shell        - Open bash shell in web container"
	@echo "  clean        - Stop services and remove volumes (WARNING: deletes data!)"
	@echo ""

# First time setup
setup:
	@if [ ! -f .env.local ]; then \
		cp .env.example .env.local; \
		echo "✓ Created .env.local from template"; \
		echo ""; \
		echo "Next steps:"; \
		echo "  1. Run 'make up-d' to start all services"; \
		echo "  2. Run 'make init-data' to load sample course data"; \
		echo ""; \
	else \
		echo "✓ .env.local already exists"; \
	fi

# Start services
up:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🚀 Starting Aether Learning Platform..."
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "📍 Services will be available at:"
	@echo "   • API Docs:  http://localhost:8000/docs"
	@echo "   • Health:    http://localhost:8000/health"
	@echo "   • API:       http://localhost:8000"
	@echo ""
	@echo "💡 Press Ctrl+C to stop services"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	docker-compose up

# Start services in background
up-d:
	docker-compose up -d
	@echo ""
	@echo "✓ Services started in background"
	@echo "  API docs: http://localhost:8000/docs"
	@echo "  Health: http://localhost:8000/health"
	@echo ""
	@echo "View logs: make logs"

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# Rebuild images
build:
	docker-compose up --build

# View logs
logs:
	docker-compose logs -f

logs-web:
	docker-compose logs -f web

logs-worker:
	docker-compose logs -f worker

logs-db:
	docker-compose logs -f db

# Database shells
db-shell:
	docker-compose exec db psql -U aether_user -d aether_db

redis-shell:
	docker-compose exec redis redis-cli

# Open bash in web container
shell:
	docker-compose exec web bash

# Run tests
test:
	docker-compose exec web uv run pytest

test-v:
	docker-compose exec web uv run pytest -v

test-cov:
	docker-compose exec web uv run pytest --cov=app --cov-report=html
	@echo ""
	@echo "Coverage report generated: htmlcov/index.html"

# Initialize development data
init-data:
	@echo "📦 Loading development course data..."
	docker-compose exec web uv run python scripts/setup_dev_course.py
	@echo ""
	@echo "✓ Development data loaded"
	@echo "  Visit http://localhost:7474 to explore Neo4j graph"

# Clean everything (WARNING: deletes volumes!)
clean:
	@echo "⚠️  WARNING: This will delete all local database data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "✓ Cleaned up"; \
	else \
		echo "Cancelled"; \
	fi

# Check service health
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ Service not responding"
