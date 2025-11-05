# Aether Learning Platform

An adaptive learning platform for Ontario high school students, powered by knowledge graphs and intelligent recommendation algorithms.

## Core Features

### 1. Knowledge Graph-Based Curriculum
[The design detail of the knowledge node](/docs/knowledge_graph.md)
- Models high school curriculum (Grade 11 Physics, Grade 12 Chemistry, etc.) as an interconnected graph
- Tracks prerequisite relationships between concepts
- Tracks subtopic for each concept node.

### 2. Mastery Tracking with BKT
[Definition of BKT](/docs/mastery_level.md)
- Implements Bayesian Knowledge Tracing to model student understanding
- Updates knowledge state after each answer
- Predicts mastery probability for each concept node

### 3. Updating Mastery Level:


### 2. Adaptive Question Recommendation
- [ ] 
- Analyzes student performance history
- Recommends problems tailored to current proficiency level
- Uses Neo4j graph traversal to find optimal next concepts



### 4. Automated Multi-Format Grading
- [ ]
- **Multiple Choice**: Instant feedback with explanation
- **Fill-in-Blank**: Case-insensitive with whitespace normalization
- **Calculation**: Tolerance-based numeric comparison
- Async processing via Redis task queue

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **API** | FastAPI + Python 3.12 |
| **Relational DB** | PostgreSQL (users, courses, submissions) |
| **Graph DB** | Neo4j (knowledge graph, mastery tracking) |
| **Task Queue** | Redis (background grading) |
| **Frontend** | iOS (SwiftUI) |
| **Package Manager** | uv |

## Architecture

```
iOS App/Frontend
   ↓ REST API
FastAPI Server
   ├─→ PostgreSQL (user data, quizzes)
   ├─→ Neo4j (knowledge graph, relationships)
   └─→ Redis Queue → Worker (async grading)
```

**Design principle**: Keep it simple. Redis for queuing, no heavy message brokers.

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Access to team's Neo4j Aura instance (get credentials from your team lead)

### Setup (First Time)

```bash
# 1. Clone the repository
git clone <repository-url>
cd aetherreload

# 2. Configure environment variables
cp .env.example .env.local
# Edit .env.local and add Neo4j Aura credentials

# 3. Start all services (PostgreSQL, Redis, API, Worker)
docker-compose up
```

- **API docs**: http://localhost:8000/docs
- **API endpoint**: http://localhost:8000

### Daily Development

```bash
# Start services
docker-compose up

# Stop services (Ctrl+C, then)
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after dependency changes
docker-compose up --build
```

### Alternative: Local Development (Without Docker)

If you prefer running the app locally:

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Start only databases
docker-compose up -d db redis

# 3. Install dependencies
uv sync

# 4. Run API server
uv run uvicorn app.main:app --reload

# 5. Run worker (separate terminal)
uv run python -m app.worker
```


## How Adaptive Learning Works

1. **Student enrolls** in a course → Creates mastery relationships in Neo4j
2. **Requests question** → Algorithm finds best concept based on:
   - Current mastery level (BKT probability)
   - Prerequisite satisfaction
   - Difficulty progression
3. **Submits answer** → Worker grades asynchronously and updates:
   - Mastery probability in Neo4j
   - Historical performance in PostgreSQL
4. **Next question** → Repeats with updated knowledge state

## Testing

```bash
uv run pytest              # Run all tests
uv run pytest -v          # Verbose mode
uv run pytest -x          # Stop on first failure
```

## License

MIT
