# Question Recommendation Algorithm

## Overview

The question recommendation algorithm selects the next knowledge node for a student based on three priorities:

1. **Review** - Spaced repetition of mastered content to prevent forgetting
2. **Remediation** - Practice on weak or struggling nodes
3. **New Learning** - Introduction of new concepts when prerequisites are met

The algorithm integrates:
- **BKT (Bayesian Knowledge Tracing)**: Tracks mastery level of each node
- **FSRS (Free Spaced Repetition Scheduler)**: Schedules optimal review intervals

---

## Data Model

### Mastery Relationship

`(User) -[HAS_MASTERY]-> (KnowledgeNode)`

**Properties:**
- `state`: Current learning state — `"learning"`, `"relearning"`, or `"review"`
- `score`: Mastery probability $P(L_t) \in [0, 1]$ computed by BKT
- `due_date`: Next review date (FSRS-based scheduling)
- `p_l0`, `p_t`, `p_g`, `p_s`: BKT parameters (see [mastery_level_kbt.md](./mastery_level_kbt.md))

### Graph Relationships

- **`IS_PREREQUISITE_FOR`**: Defines prerequisite dependencies between nodes
- **`HAS_SUBTOPIC`**: Hierarchical decomposition of topics (see [knowledge_graph.md](./knowledge_graph.md))
- **`TESTS`**: Links questions to knowledge nodes

---

## Selection Algorithm

The algorithm follows a strict priority cascade:

### Priority 1: Review

**Trigger:** Always check first.

**Goal:** Maintain retention of previously mastered material.

**Steps:**
1. Find all knowledge nodes where `state = "review"` and `due_date <= current_date`
2. Sort by `due_date` (earliest due date first)
3. Return the most overdue node

**Result:** If a review node is found, recommend it immediately and stop. Otherwise, proceed to Priority 2.

---

### Priority 2: Remediation

**Trigger:** Only if no review nodes are due.

**Goal:** Strengthen weak or struggling nodes.

**Steps:**
1. Find all knowledge nodes where `state IN ["learning", "relearning"]`
2. Sort by:
   - `level` (ASC) — Lower-level nodes first (foundational concepts)
   - `dependents_count` (DESC) — Nodes with more dependents (unlock more content)
   - `score` (ASC) — Weakest mastery first
3. Return the highest priority weak node

**Result:** If a weak node is found, recommend it and stop. Otherwise, proceed to Priority 3.

---

### Priority 3: New Knowledge

**Trigger:** Only if no review or remediation nodes are available.

**Goal:** Introduce new concepts when prerequisites are met.

**Steps:**
1. Find all knowledge nodes where:
   - User has no `HAS_MASTERY` relationship (never studied)
   - Node has at least one linked question
2. For each candidate node:
   - Check all prerequisite nodes
   - Verify all prerequisites are mastered: `score >= threshold` (typically 0.7) OR `state = "review"`
   - Calculate **quality score** = weighted average of prerequisite mastery scores
   - If node has no prerequisites, assign quality = 1.0
3. Keep only nodes where **all** prerequisites are mastered
4. Sort by:
   - `level` (ASC) — Shallower nodes first (breadth-first learning)
   - `dependents_count` (DESC) — Nodes that unlock more content
   - `quality` (DESC) — Better prerequisite mastery
5. Return the highest priority new node

**Result:** Recommend the new knowledge node, or return `None` if no eligible nodes exist.

---

## FSRS Integration

FSRS (Free Spaced Repetition Scheduler) manages review timing based on the forgetting curve:

$$R(t) = e^{-t/S}$$

**Where:**
- $R(t)$ = Retrievability at time $t$
- $t$ = Time elapsed since last review
- $S$ = Stability (memory strength in days)

**Key Parameters:**
- **Stability**: Increases with successful reviews
- **Difficulty**: Personalized per user and node
- **Retrievability**: When $R(t)$ drops below threshold (e.g., 0.9), schedule review

**FSRS Rating Mapping:**
- Incorrect answer → `AGAIN` (relearn)
- Correct + low mastery (< 0.65) → `HARD`
- Correct + medium mastery (0.65-0.85) → `GOOD`
- Correct + high mastery (> 0.85) → `EASY`

---

## Question Selection

Once a node is selected, choose a specific question:

**Difficulty Matching:**
- Low mastery (< 0.3) → Easy questions
- Medium mastery (0.3-0.6) → Medium questions
- High mastery (> 0.6) → Hard questions

**Freshness:**
- Avoid recently seen questions (track last N attempts)
- Prefer questions not seen in recent history

---

## Special Cases

### New User (No Mastery Data)

**Solution:** Find nodes with no prerequisites (foundation nodes) and start with easy questions to establish baseline.

### No Available Nodes (Stuck)

**Solution:** Identify weak nodes blocking the most prepared nodes. Prioritize remediation of high-impact blocking nodes.

### All Content Mastered

**Solution:** Focus on FSRS-scheduled reviews and hard questions on advanced topics.

### Incorrect Answer (Diagnostic)

**Solution:** Test prerequisite nodes directly to identify root cause. See [mastery_level_propagation.md](./mastery_level_propagation.md) for details.