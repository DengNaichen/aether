.PHONY: help up down restart logs shell test clean build deploy

# Configuration
PROJECT_ID ?= airy-web-476402-f4
REGION ?= northamerica-northeast2
REPOSITORY ?= aether
SERVICE_NAME ?= aether
IMAGE_NAME = $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPOSITORY)/aether-app

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
	@echo ""
	@echo "Database:"
	@echo "  init-data    - Initialize development data (course + knowledge graph)"
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
	@echo "Deployment (Google Cloud Run):"
	@echo "  gcp-setup    - Setup GCP project and enable required APIs"
	@echo "  gcp-build    - Build and push Docker image to Artifact Registry"
	@echo "  gcp-deploy   - Deploy to Cloud Run (requires env.yaml)"
	@echo "  gcp-logs     - View Cloud Run logs"
	@echo "  gcp-url      - Get the deployed service URL"
	@echo "  gcp-status   - Check Cloud Run service status"
	@echo "  deploy-all   - Build and deploy in one command"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint         - Run ruff linter"
	@echo "  lint-fix     - Run ruff linter and auto-fix"
	@echo "  format       - Run ruff formatter"
	@echo "  format-check - Check formatting without fixing"
	@echo "  quality      - Run all quality checks (lint + format-check)"
	@echo ""
	@echo "Pre-commit:"
	@echo "  pre-commit-install - Install pre-commit hooks"
	@echo "  pre-commit-run     - Run all hooks on all files"
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
	@if [ ! -f .env.local ]; then \
		echo "❌ Error: .env.local not found!"; \
		echo "Please run 'make setup' first or create .env.local manually."; \
		exit 1; \
	fi
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
	docker-compose up --build

# Start services in background
up-d:
	@if [ ! -f .env.local ]; then \
		echo "❌ Error: .env.local not found!"; \
		echo "Please run 'make setup' first or create .env.local manually."; \
		exit 1; \
	fi
	docker-compose up -d --build
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

# Open bash in web container
shell:
	docker-compose exec web bash

# ================================
# Testing Commands
# ================================

# Start test database services
test-up:
	@if [ ! -f .env.test ]; then \
		echo "❌ Error: .env.test not found!"; \
		echo "Please create .env.test from .env.example first."; \
		exit 1; \
	fi
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🧪 Starting isolated test database services..."
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	docker-compose -f docker-compose.test.yml up -d
	@echo ""
	@echo "✓ Test services started:"
	@echo "  • PostgreSQL:  localhost:5433"
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
	@if [ ! -f .env.test ]; then \
		echo "❌ Error: .env.test not found!"; \
		exit 1; \
	fi
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🧪 Running tests..."
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	ENVIRONMENT=test uv run pytest
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

# ================================
# Code Quality & Linting
# ================================

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

quality: lint format-check

# ================================
# Pre-commit Hooks
# ================================

pre-commit-install:
	uv run pre-commit install

pre-commit-run:
	uv run pre-commit run --all-files

# Show status of all database containers
status:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "📊 Database Services Status"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "🔧 Development (Client):"
	@docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  No development services running"
	@echo ""
	@echo "🧪 Test Databases:"
	@docker-compose -f docker-compose.test.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  No test databases running"
	@echo ""
	@echo "💡 Quick Reference:"
	@echo "   Development: Uses host machine services (Supabase, local scripts)"
	@echo "   Test:        localhost:5433 (PostgreSQL)"

# ================================
# Google Cloud Run Deployment
# ================================

# Setup GCP project and enable required APIs
gcp-setup:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🔧 Setting up Google Cloud Project"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "Project ID: $(PROJECT_ID)"
	@echo "Region: $(REGION)"
	@echo ""
	@echo "Enabling required APIs..."
	gcloud services enable \
		run.googleapis.com \
		cloudbuild.googleapis.com \
		artifactregistry.googleapis.com \
		--project=$(PROJECT_ID)
	@echo ""
	@echo "Creating Artifact Registry repository (if not exists)..."
	gcloud artifacts repositories create $(REPOSITORY) \
		--repository-format=docker \
		--location=$(REGION) \
		--description="Aether Learning Platform Docker images" \
		--project=$(PROJECT_ID) 2>/dev/null || echo "Repository already exists"
	@echo ""
	@echo "✓ GCP setup completed"

# Build and push Docker image using Cloud Build
gcp-build:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🏗️  Building and pushing Docker image"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "Image: $(IMAGE_NAME):latest"
	@echo ""
	gcloud builds submit \
		--config=cloudbuild.yaml \
		--project=$(PROJECT_ID)
	@echo ""
	@echo "✓ Image built and pushed successfully"

# Deploy to Cloud Run
gcp-deploy:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🚀 Deploying to Google Cloud Run"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@if [ ! -f env.yaml ]; then \
		echo "❌ Error: env.yaml file not found!"; \
		echo ""; \
		echo "Please create env.yaml with your production environment variables."; \
		echo "See https://cloud.google.com/run/docs/configuring/environment-variables#yaml"; \
		exit 1; \
	fi
	@echo "Service: $(SERVICE_NAME)"
	@echo "Region: $(REGION)"
	@echo ""
	gcloud run deploy $(SERVICE_NAME) \
		--image=$(IMAGE_NAME):latest \
		--platform=managed \
		--region=$(REGION) \
		--allow-unauthenticated \
		--port=8000 \
		--memory=2Gi \
		--cpu=2 \
		--timeout=300 \
		--max-instances=10 \
		--min-instances=0 \
		--env-vars-file=env.yaml \
		--project=$(PROJECT_ID)
	@echo ""
	@echo "✓ Deployment completed!"
	@echo ""
	@make gcp-url

# Build and deploy in one command
deploy-all:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🚀 Complete Deployment Pipeline"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@make gcp-build
	@echo ""
	@make gcp-deploy

# View Cloud Run logs
gcp-logs:
	@echo "📋 Viewing Cloud Run logs (press Ctrl+C to exit)..."
	@echo ""
	gcloud run services logs tail $(SERVICE_NAME) \
		--region=$(REGION) \
		--project=$(PROJECT_ID)

# Get the deployed service URL
gcp-url:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🌐 Service URL"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@gcloud run services describe $(SERVICE_NAME) \
		--region=$(REGION) \
		--project=$(PROJECT_ID) \
		--format='value(status.url)' 2>/dev/null | \
		awk '{print "API URL:  " $$1 "\nAPI Docs: " $$1 "/docs\nHealth:   " $$1 "/health"}'
	@echo ""

# Check Cloud Run service status
gcp-status:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "📊 Cloud Run Service Status"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	gcloud run services describe $(SERVICE_NAME) \
		--region=$(REGION) \
		--project=$(PROJECT_ID) \
		--format='table(status.conditions.type,status.conditions.status,status.url)'
	@echo ""
	@echo "Recent revisions:"
	gcloud run revisions list \
		--service=$(SERVICE_NAME) \
		--region=$(REGION) \
		--project=$(PROJECT_ID) \
		--limit=5 \
		--format='table(metadata.name,status.conditions.status,metadata.creationTimestamp)'

# Update environment variables without redeploying
gcp-update-env:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🔄 Updating environment variables"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@if [ ! -f env.yaml ]; then \
		echo "❌ Error: env.yaml file not found!"; \
		exit 1; \
	fi
	gcloud run services update $(SERVICE_NAME) \
		--region=$(REGION) \
		--env-vars-file=env.yaml \
		--project=$(PROJECT_ID)
	@echo ""
	@echo "✓ Environment variables updated"

# Delete the Cloud Run service
gcp-delete:
	@echo "⚠️  WARNING: This will delete the Cloud Run service!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		gcloud run services delete $(SERVICE_NAME) \
			--region=$(REGION) \
			--project=$(PROJECT_ID); \
		echo "✓ Service deleted"; \
	else \
		echo "Cancelled"; \
	fi
