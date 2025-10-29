# Backend Development Roadmap

This is an **adaptive learning platform** for Ontario high school students that uses **Machine Learning** and **knowledge graphs** to personalize education. Instead of giving every student the same questions in the same order, This project analyzes each 
student's understanding and recommends the optimal next question to maximize learning 
efficiency.

## Core Problem It Solves

**Traditional learning platforms are one-size-fits-all:**
- Student A struggles with basic kinematics but gets forced into advanced dynamics
- Student B already understands velocity but wastes time on repetitive easy questions
- No system to detect prerequisite gaps (e.g., can't do friction problems because 
  force concepts are weak)

**Our solution:**
- Tracks mastery level for every concept using Bayesian Knowledge Tracing (BKT)
- Recommends questions in your "learning zone" (not too easy, not too hard)
- Detects prerequisite gaps and fills them before moving forward
- Adapts difficulty based on your performance

## How It Works (Student Perspective)

1. **Enroll in a course** (e.g., Grade 11 Physics - SPH3U)
2. **Start a quiz** → System analyzes your mastery levels across all topics
3. **Get adaptive questions** → Algorithm selects optimal concepts to test based on:
   - What you already know vs. what you're struggling with
   - Whether prerequisites are satisfied
   - When you last practiced each concept (spaced repetition)
4. **Submit answers** → System grades automatically and updates mastery levels
5. **Repeat** → Each new question is perfectly calibrated to your current level.




## Implementation Status

| Component | Status | Tests | Priority |
|-----------|--------|-------|----------|
| User Authentication & Authorization | ✓ Complete | ✓ | - |
| Course Management | ✓ Complete | ✓ | - |
| Quiz & Submission System | ✓ Complete | ✓ | - |
| Multi-Format Grading (MC, Fill-in, Calc) | ✓ Complete | ✓ | - |
| Async Worker System (Redis) | ✓ Complete | ✓ | - |
| Knowledge Graph (Neo4j) | ✓ Complete | ✓ | - |
| Bulk CSV Import | ✓ Complete | ✓ | - |
| **BKT Algorithm** | ⚠️ Stub only | ✗ | **HIGH** |
| **Mastery Propagation** | ⚠️ Stub only | ✗ | **HIGH** |
| **Adaptive Question Engine** | ⚠️ Random only | ✗ | **Medium** |
| Sign with Google| ✗ Not started| ✗ | MEDIUM |
| Sign with Apple| ✗ Not started| ✗ | MEDIUM |
| Mastery Visualization API | ✗ Not started | ✗ | MEDIUM |
| Learning Analytics | ✗ Not started | ✗ | MEDIUM |
| Spaced Repetition | ✗ Not started | ✗ | LOW |

---
## Phase 0： Decide if add `User` Node in `neo4j` database[ARCH#1]

Will use [ARCH] as keyword for discuss the architecture of this project. 

| Solution | Storage Location |  Advantages | Disadvantages |
| ---------- | -------------- | -------|-------- |
| **A. Store in Neo4j** | Neo4j  | - Can be used directly in graph algorithms (e.g., recommendation paths, mastery-weighted shortest paths)<br>- Enables user-subgraph reasoning (similar users, personalized learning paths)<br>- No need for cross-database access | - Relationship explosion when user count is large (N_user × N_concept)<br>- Poor performance with frequent updates<br>- Numerical aggregation (average, distribution) less efficient than in SQL |
| **B. Store in SQL** | SQL | - Simple and efficient for frequent updates<br>- Supports batch analysis and statistics<br>- Can be combined with caching or streaming updates | - Cannot be used directly in graph algorithms<br>- Requires data sync or temporary import to Neo4j before recommendations |

The implementation right now is A.

## Phase 1: Design a small but high quality knowledge graph.
Will use [KGC] as keyword for knowledge graph construction.

- [ ] [KGC#1] Design a small knowledge graph schema based on the [updated documentation](/docs/knowledge_graph.md)
- [ ] [KGC#2] Build a sample knowledge graph for a high school course (or a few selected chapters)
- [ ] [KGC#3] Create a script to import CSV data into [Neo4j Aura](https://neo4j.com/product/auradb/) for testing and shared use


## Phase 2: BKT Foundation and redesign the course management. 

Will use [BKT#1] as keyword for BKT algorithm design and implementation. 

- [ ] [BKT#2]Replace basic mastery stub with proper Bayesian Knowledge Tracing

### What's Currently Broken

**Current implementation** ([app/worker/handlers.py](app/worker/handlers.py)):
```python
def _update_mastery_level(neo_user, knode, is_correct, user_id_str):
    rel = neo_user.mastery.relationship(knode)
    if not rel:
        rel = neo_user.mastery.connect(knode)

    # STUB: Just sets 0.9 for correct, 0.2 for incorrect
    rel.score = 0.9 if is_correct else 0.2
    rel.last_update = datetime.now(timezone.utc)
    rel.save()
```

This completely ignores:
- Prior knowledge
- Learning from practice
- Guessing probability
- Slip (careless mistakes)
- Forgetting curve

### Tasks

- [ ] [BKT#3]**Extend Neo4j Model** ([app/models/neo4j_model.py](app/models/neo4j_model.py))

- [ ] [BKT#4]**Create BKT Calculator** (NEW FILE: `app/algorithms/bkt.py`)


- [ ] [BKT#5]**Replace Stub in Grading Handler** ([app/worker/handlers.py](app/worker/handlers.py))


- [ ] [BKT#6]**Write Comprehensive Tests** (NEW FILE: `tests/test_bkt.py`)
  - Test correct answer update (mastery increases)
  - Test incorrect answer update (mastery decreases)
  - Test learning transition applies
  - Test mastery converges to 0.9+ after 10 correct answers
  - Test mastery decreases appropriately for incorrect answers
  - Test forgetting curve decay
  - Test edge cases (mastery = 0, mastery = 1)
  - Test parameter validation