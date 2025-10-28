# Aether Learning Platform

An adaptive learning platform for Ontario high school students, powered by knowledge graphs and intelligent recommendation algorithms.

## Core Features

### 1. Knowledge Graph-Based Curriculum
- Models Ontario curriculum (Physics SPH3U, Chemistry SCH3U, etc.) as an interconnected graph
- Tracks prerequisite relationships between concepts
- Enables intelligent pathfinding for personalized learning sequences

### 2. Adaptive Question Recommendation
- Analyzes student performance history
- Recommends problems tailored to current proficiency level
- Uses Neo4j graph traversal to find optimal next concepts

### 3. Mastery Tracking with BKT
- Implements Bayesian Knowledge Tracing to model student understanding
- Updates knowledge state after each answer
- Predicts mastery probability for each concept node

### 4. Automated Multi-Format Grading
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
iOS App
   ↓ REST API
FastAPI Server
   ├─→ PostgreSQL (user data, quizzes)
   ├─→ Neo4j (knowledge graph, relationships)
   └─→ Redis Queue → Worker (async grading)
```

**Design principle**: Keep it simple. Redis for queuing, no heavy message brokers.

## Quick Start

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Start databases
docker-compose up -d

# 3. Install dependencies
uv sync

# 4. Run API server
uv run uvicorn app.main:app --reload

# 5. Run worker (separate terminal)
uv run python -m app.worker.worker
```

API docs: http://localhost:8000/docs

## Key Endpoints

```
POST /users/register          # Sign up
POST /users/login             # Get JWT token
GET  /questions/random        # Get adaptive question
POST /submissions             # Submit answer (async graded)
GET  /courses/{id}            # Course with knowledge graph
POST /courses/{id}/enroll     # Enroll and initialize mastery
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

## Bulk Import

Import curriculum via CSV:

```bash
# Knowledge nodes
curl -X POST http://localhost:8000/knowledge-nodes/bulk-import \
  -F "file=@nodes.csv" -F "course_code=SPH3U"

# Questions
curl -X POST http://localhost:8000/questions/bulk-import \
  -F "file=@questions.csv"

# Concept relationships
curl -X POST http://localhost:8000/relations/bulk-import \
  -F "file=@relations.csv"
```

See `example_data/` for CSV formats.

## Testing

```bash
uv run pytest              # Run all tests
uv run pytest -v          # Verbose mode
uv run pytest -x          # Stop on first failure
```

**138 tests, 97% pass rate**

## Project Structure

```
app/
├── core/          # Config, database, security
├── models/        # SQLAlchemy + Neo4j models
├── routes/        # API endpoints
├── worker/        # Async task handlers
│   ├── worker.py           # Main worker loop
│   ├── handlers.py         # Grading logic
│   └── bulk_import_handlers.py
└── main.py        # FastAPI app
```

## Why This Stack?

- **Neo4j**: Perfect for modeling curriculum graphs and traversing concept relationships
- **PostgreSQL**: Battle-tested for transactional data (users, submissions)
- **Redis**: Lightweight queue, no need for RabbitMQ complexity
- **uv**: 460x faster than conda (0.13s vs 60s for dependencies)
- **FastAPI**: Modern async Python, auto-generated docs

## License

MIT

---

**Built for Ontario high school students**
