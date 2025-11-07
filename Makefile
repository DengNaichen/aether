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
	@echo "  test-up      - Start isolated test database services"
	@echo "  test-down    - Stop test database services"
	@echo "  test         - Run all tests (requires test-up first)"
	@echo "  test-v       - Run tests (verbose)"
	@echo "  test-cov     - Run tests with coverage report"
	@echo "  test-all     - Start test services, run tests, then stop"
	@echo "  test-shell   - Connect to test database shells"
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

# ================================
# Testing Commands
# ================================

# Start test database services
test-up:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🧪 Starting isolated test database services..."
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	docker-compose -f docker-compose.test.yml up -d
	@echo ""
	@echo "✓ Test services started:"
	@echo "  • PostgreSQL:  localhost:5433"
	@echo "  • Redis:       localhost:6380"
	@echo "  • Neo4j HTTP:  localhost:7475"
	@echo "  • Neo4j Bolt:  localhost:7688"
	@echo ""
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@echo ""
	@echo "✓ Ready to run tests with: make test"

# Stop test database services
test-down:
	@echo "🛑 Stopping test database services..."
	docker-compose -f docker-compose.test.yml down
	@echo "✓ Test services stopped"

# Run tests (requires test services to be running)
test:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🧪 Running tests..."
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	uv run pytest
	@echo ""
	@echo "✓ Tests completed"

test-v:
	@echo "🧪 Running tests (verbose)..."
	uv run pytest -v

test-cov:
	@echo "🧪 Running tests with coverage..."
	uv run pytest --cov=app --cov-report=html --cov-report=term
	@echo ""
	@echo "✓ Coverage report generated: htmlcov/index.html"

# Run complete test cycle (up -> test -> down)
test-all:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🧪 Running complete test cycle..."
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@make test-up
	@echo ""
	@make test
	@echo ""
	@make test-down
	@echo ""
	@echo "✓ Test cycle completed"

# Connect to test databases
test-db-shell:
	@echo "🔌 Connecting to test PostgreSQL..."
	docker-compose -f docker-compose.test.yml exec test-db psql -U aether_user -d aether_test_db

test-redis-shell:
	@echo "🔌 Connecting to test Redis..."
	docker-compose -f docker-compose.test.yml exec test-redis redis-cli

# Clean test volumes (WARNING: deletes test data!)
test-clean:
	@echo "⚠️  WARNING: This will delete all test database data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose -f docker-compose.test.yml down -v; \
		echo "✓ Test data cleaned up"; \
	else \
		echo "Cancelled"; \
	fi

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

# Show status of all database containers
status:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "📊 Database Services Status"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "🔧 Development Databases:"
	@docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | grep -E "db|redis|neo4j" || echo "  No development databases running"
	@echo ""
	@echo "🧪 Test Databases:"
	@docker-compose -f docker-compose.test.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  No test databases running"
	@echo ""
	@echo "💡 Quick Reference:"
	@echo "   Development: localhost:5432 (PostgreSQL), localhost:6379 (Redis), localhost:7474/7687 (Neo4j)"
	@echo "   Test:        localhost:5433 (PostgreSQL), localhost:6380 (Redis), localhost:7475/7688 (Neo4j)"
