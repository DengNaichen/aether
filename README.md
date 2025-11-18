# Aether

**An intelligent knowledge management platform that helps you master any subject through adaptive learning and knowledge graphs.**

Map any domain of knowledge, track your mastery using Machine Learning, and learn efficiently with scientifically-optimized review scheduling.

---

## The Problem

Traditional learning tools are either too rigid or too manual:
- **Anki**: Great for flashcards, but no concept relationships or prerequisite tracking
- **Notion**: Good for notes, but doesn't guide what to learn next
- **Online courses**: Fixed curricula that don't adapt to your knowledge gaps
- **Roam Research**: Knowledge graphs, but manual tracking and no spaced repetition

## The Solution

**Aether combines the best of all worlds:**

1. **Knowledge Graphs** (like Roam) - Map interconnected concepts with prerequisites and hierarchies
2. **Adaptive Learning** (like Duolingo) - AI recommends optimal next question based on your knowledge state
3. **Bayesian Knowledge Tracing (BKT)** - Probabilistic mastery modeling for every concept
4. **Spaced Repetition (FSRS)** - Memory-optimized review scheduling based on forgetting curves
5. **User-Generated Content** (like Wikipedia) - Create and share knowledge graphs for any topic

**Use Aether for:**
- 🖥️ **Programming**: Build a "System Design" or "React Patterns" skill tree
- 🌍 **Languages**: Create "Spanish Grammar" or "Japanese Kanji" concept maps
- 📚 **Academics**: Organize "Calculus" or "Organic Chemistry" knowledge
- 🎵 **Creative Skills**: Map "Music Theory" or "Photography Techniques"
- 💼 **Professional Growth**: Track "AWS Certification" or "Product Management" prep
- 🧠 **Personal Knowledge**: Build your own second brain for anything you're learning

---

## How It Works

### For Learners

1. **Browse or create** a knowledge graph for your topic
2. **Enroll** → System initializes your mastery tracking
3. **Get adaptive questions** → AI selects optimal concepts based on:
   - Your current mastery levels across all topics
   - Prerequisite dependencies (learn foundations first)
   - Spaced repetition timing (review before you forget)
4. **Submit answers** → Automatic grading + Bayesian mastery updates
5. **Repeat** → Each question adapts to your evolving knowledge state

### For Creators

1. **Create knowledge graph** (public or private)
2. **Design structure**:
   - Add knowledge nodes (concepts/topics)
   - Define prerequisite relationships (A must be learned before B)
   - Organize subtopic hierarchies (parent-child decomposition)
3. **Add questions** (multiple choice, fill-in-the-blank, calculation)
4. **Share** → Publish for the community, or keep for personal use
5. **Iterate** → Enroll yourself to test the learning experience

### Algorithm Flow

```
Question Request
    ↓
Phase 1: FSRS Filtering
  └─ Find nodes due for review based on spaced repetition
    ↓
Phase 2: BKT Sorting
  └─ Prioritize by prerequisites, level, mastery gap, impact
    ↓
Phase 3: New Learning
  └─ If no reviews due, teach new concepts (prerequisites mastered)
    ↓
Return Optimal Question
    ↓
Student Submits Answer
    ↓
BKT Update (Bayesian inference on mastery probability)
    ↓
FSRS Scheduling (calculate next review date)
```

---

## Core Features

### 1. Knowledge Graph Creation & Management
[Design Documentation](/docs/algorithms/knowledge_graph.md)

**User-Created Curricula:**
- **Create custom knowledge graphs** for any subject or skill
- **Public/Private control**: Share with the world or keep for personal use
- **Template graphs**: Official curriculum standards (e.g., Ontario SPH3U Physics)

**Graph Structure:**
- **Knowledge Nodes**: Individual concepts/topics
- **Prerequisites**: Directed relationships (A → B means A must be learned before B)
- **Subtopics**: Hierarchical parent-child decomposition
- **Leaf Node Rule**: Only atomic leaf nodes can have prerequisites (ensures precise diagnosis)

**Use Cases:**
- Software engineers mapping technical skills and certifications
- Language learners organizing vocabulary and grammar concepts
- Students preparing for exams with custom study graphs
- Professionals tracking career development competencies
- Hobbyists building expertise in music, art, or crafts
- Teams creating shared knowledge bases for onboarding

### 2. Bayesian Knowledge Tracing (BKT)
[Algorithm Documentation](/docs/algorithms/mastery_level_kbt.md)

Probabilistic model tracking per-concept mastery:
- **p_l**: Current mastery probability (0.0-1.0)
- **p_t**: Learning transition probability (improvement rate)
- **p_g**: Guess probability (question-specific)
- **p_s**: Slip probability (careless mistake rate)

Updates knowledge state after each answer using Bayesian inference.

### 3. Free Spaced Repetition Scheduler (FSRS)

Memory-optimized review scheduling:
- **FSRS State Machine**: Learning → Review → Relearning
- **Stability Tracking**: Long-term memory retention modeling
- **Difficulty Rating**: Adaptive 1.0-10.0 scale per concept
- **Due Date Calculation**: Optimal review timing based on forgetting curve

### 4. Hybrid Adaptive Recommendation
[Algorithm Documentation](/docs/algorithms/question_recommendation.md)

**Phase 1 (FSRS)**: Find nodes due for review

**Phase 2 (BKT)**: Sort due nodes by:
- Prerequisite satisfaction (check dependencies first)
- Topological level (foundation before advanced)
- Mastery gap (prioritize struggling concepts)
- Dependent count (high-impact nodes first)
- Days overdue (respect FSRS schedule)

**Phase 3 (New Learning)**: If no reviews due, recommend new concepts where prerequisites are mastered (≥0.6)

### 5. Multi-Format Question Support

- **Multiple Choice**: Index-based answer matching
- **Fill-in-the-Blank**: Case-insensitive text matching with multiple accepted answers
- **Calculation**: Numerical comparison with configurable precision

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **API Framework** | FastAPI 0.117.1 + Python 3.12 |
| **Database** | PostgreSQL 15 (all data + knowledge graphs) |
| **ORM** | SQLAlchemy 2.0.43 (async) |
| **Authentication** | JWT (python-jose) + bcrypt |
| **Algorithms** | Custom BKT + FSRS implementation |
| **Email** | fastapi-mail, Resend API |
| **Server** | Uvicorn with uvloop |
| **Package Manager** | uv |
| **Frontend** | Web (Next.js + React) - in development |

## Architecture

```
Web App (Next.js + React)
    ↓ REST API
FastAPI Server
    ↓
PostgreSQL
  ├─ Users & Authentication
  ├─ Knowledge Graphs (nodes, prerequisites, subtopics)
  ├─ Questions (MC, fill-in, calculation)
  ├─ User Mastery (BKT parameters + FSRS state)
  └─ Enrollments & Activity Tracking
```

**Design Philosophy**:
- **PostgreSQL for Everything**: Migrated from Neo4j for simpler deployment and maintenance
- **Optimized for Local Traversal**: Algorithms only need 1-2 hop queries
- **Async-First**: Full async/await support for concurrent requests

---

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### Setup (First Time)

```bash
# 1. Clone the repository
git clone <repository-url>
cd aether

# 2. Configure environment variables
cp .env.example .env.local

# 3. Start all services (PostgreSQL, API)
docker-compose up -d

# 4. Initialize development data (template graphs, sample questions)
docker-compose exec web uv run python scripts/setup_dev_data_pg.py
```

**Access Points:**
- API Documentation: http://localhost:8000/docs
- API Endpoint: http://localhost:8000

### Daily Development

```bash
# Start services
docker-compose up
# or
make up

# Stop services (Ctrl+C, then)
docker-compose down
# or
make down

# View logs
docker-compose logs -f web

# Rebuild after dependency changes
docker-compose up --build
```

### Testing

```bash
# Start test environment
make test-up

# Run tests
uv run pytest              # All tests
uv run pytest -v          # Verbose mode
uv run pytest -x          # Stop on first failure
uv run pytest tests/test_bkt.py  # Specific test file
```

---

## API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login (JWT)
- `POST /refresh` - Refresh access token
- `POST /forgot-password` - Password reset request
- `POST /reset-password` - Complete password reset

### Knowledge Graph Management
- `POST /me/graphs` - Create custom knowledge graph
- `POST /me/graphs/{graph_id}/enrollments` - Enroll in your own graph
- `GET /graphs/templates` - Get all template graphs
- `POST /graphs/{graph_id}/enrollments` - Enroll in public/template graph

### Graph Structure (Owner Only)
- `POST /graphs/{graph_id}/nodes` - Create knowledge node
- `POST /graphs/{graph_id}/prerequisites` - Create prerequisite relationship
- `POST /graphs/{graph_id}/subtopics` - Create subtopic relationship
- `GET /graphs/{graph_id}/graph-viz` - Visualize graph structure

### Questions & Learning
- `POST /me/graphs/{graph_id}/questions` - Create question
- `POST /me/graphs/{graph_id}/next-question` - Get adaptive recommendation
- `POST /answer` - Submit answer (grades + updates mastery)

---

## Key Design Decisions

1. **PostgreSQL over Neo4j**: Simpler deployment, better numerical operations, sufficient for 1-2 hop queries
2. **BKT + FSRS Hybrid**: BKT tracks mastery, FSRS schedules reviews (independent systems working together)
3. **Leaf Node Prerequisites**: Only atomic concepts have prerequisites (precise knowledge diagnosis)
4. **User-Generated Content**: Anyone can create and share knowledge graphs (democratize curriculum design)
5. **Triple-Key Mastery**: (user_id, graph_id, node_id) enables learning across multiple graphs simultaneously

---

## Learning Flow Example

**Scenario**: Developer learning "System Design" knowledge graph

1. **Enrollment**:
   - Creates `GraphEnrollment` record
   - Initializes `UserMastery` for all nodes (score=0.1, p_l0=0.2, p_t=0.2, FSRS state=Learning)

2. **First Question Request**:
   - Phase 1 (FSRS): All nodes overdue (just enrolled)
   - Phase 2 (BKT): Selects "Load Balancing" (level=0, no prerequisites)
   - Returns question about load balancer types

3. **User Answers Correctly**:
   - BKT updates mastery: 0.1 → 0.35 (Bayesian inference)
   - FSRS updates: due_date = now + 1 day, stability increases

4. **Second Question Request**:
   - Phase 1 (FSRS): Most nodes still overdue
   - Phase 2 (BKT): Selects "Caching Strategies" (prerequisite "HTTP Fundamentals" not mastered yet, but highest priority)
   - Returns caching question

5. **After Several Correct Answers on Load Balancing**:
   - Load Balancing mastery reaches 0.65 (≥0.6 threshold)
   - Algorithm now recommends "Distributed Caching" (prerequisite: Load Balancing ✓, Caching ✓)

6. **One Week Later**:
   - FSRS detects Load Balancing is due for review
   - Phase 1 returns Load Balancing for spaced repetition
   - Strengthens long-term memory retention

---

## Project Status

### ✅ Completed
- User authentication & authorization (JWT)
- Knowledge graph creation & management
- User-generated curricula (public/private graphs)
- Multi-format questions (MC, fill-in, calculation)
- BKT algorithm implementation
- FSRS scheduling integration
- Hybrid adaptive recommendation engine
- Single answer submission with immediate grading
- PostgreSQL migration (from Neo4j)

### 🚧 In Progress
- **Web Frontend** (React/Next.js) - Knowledge graph builder + learning interface
- Mastery propagation (update prerequisites/parents after answering)
- Graph search & discovery
- Category system for organizing graphs

### 📋 Planned
- Learning analytics dashboard
- Graph forking & remixing
- Collaborative graph editing
- OAuth integration (Google/GitHub/Apple)
- AI-assisted graph creation
- Export to Anki, Obsidian, Notion
- Mobile apps (lower priority)

---

## Contributing

This is a personal learning project, but contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Submit a pull request

---

## License

MIT
