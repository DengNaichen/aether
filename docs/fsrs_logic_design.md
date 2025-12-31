# Pure FSRS Mastery & Propagation Design

## 1. Core Philosophy: Retrievability is Mastery
We treat FSRS **Retrievability (R)** as the mastery signal: “What is the probability the user can recall this skill right now?”

**Formula**:
$$
R(t) = 0.9^{\frac{\Delta t}{S}}
$$

*   $t$: Current time
*   $\Delta t$: Time elapsed since last review
*   $S$: Memory Stability (in days)

**Why this logic is smoother**:
A student who "mastered" a topic 3 months ago but hasn't reviewed it *should* have a lower mastery score today than a student who mastered it yesterday. BKT fails to capture this; FSRS captures it naturally.

## 2. The Logic Flow

### A. Leaf Nodes Only (Atomic Concepts)
These are the only nodes tracked in FSRS (questions attach to leaf nodes).
*   **Storage (`user_mastery`)**: `fsrs_state`, `fsrs_stability`, `fsrs_difficulty`, `due_date`, `last_review`, `cached_retrievability`, `review_log`.
*   **Score**: `cached_retrievability` is a snapshot for fast reads; real-time $R(t)$ can be recomputed from the FSRS card when needed.
*   **Update**: Direct reviews call `Scheduler.review_card`, then persist the new stability/difficulty/due and append a log entry.

### B. Parent Nodes
Parent aggregation has been removed. No FSRS state is stored or rolled up for parents; dashboards should rely on leaf data only (aggregate in the UI if needed).

### C. Backward Propagation (The "Implicit Review")
This is the mechanism for updating prerequisites without forcing redundant reviews.

**Scenario**:
*   Node A (Basic Algebra) is a prerequisite for Node B (Calculus).
*   User answers a question for Node B correctly.

**The Logic Chain**:
1.  To solve B, the user *must* have successfully retrieved concept A.
2.  Therefore, the user has effectively "reviewed" A, even if they didn't see a card for A.
3.  We treat this as a "Passive Review" of A.

**Algorithm**:
1.  **Trigger**: User gets `Node B` Correct.
2.  **Identify**: Find all distinct prerequisites $P_1, P_2...$ of `Node B`.
3.  **Action**: For each Prerequisite $P$:
    *   Execute `fsrs.review_card(card=P, rating=Good, now=time)`
    *   **Result**: $P.stability$ increases; $P.due\_date$ is pushed to the future.
4.  **benefit**: The scheduling system automatically "silences" specific reviews for basics (Algebra) as long as the user is performing well on advanced topics (Calculus).

### D. Attenuation: Stochastic Implicit Review
**Problem**: Answering a Calculus question uses *some* Algebra, but maybe not *all* of it. A full strength review for Algebra might overestimate mastery.
**Solution**: Use **Probabilistic Decay**. Instead of scaling the *strength* of the review (which breaks FSRS math), we scale the *probability* of the review occurring.

**Formula**:
$$ P(Review) = 0.5^{depth} $$
*   **Depth 1 (Direct Prereq)**: 50% chance to trigger review. (Or maybe 100% if very strong correlation)
*   **Depth 2**: 25% chance.
*   **Depth 3**: 12.5% chance.

**Why this works**: Over time, the *expected value* of the stability increase is exactly proportional to the coupling strength. It's mathematically sound and computationally simple.

## 3. Propagation Example

**State T0**:
*   **User**: Knows "Addition" ($S=10$ days).
*   **Action**: User starts learning "Multiplication" (which depends on Addition).

**Event**:
*   User answers a "Multiplication" question correctly.

**Effect**:
1.  **Multiplication Node**:
    *   FSRS Update: $S$ increases from $0 \to 1$ day (New -> Learning).
    *   Mastery: $R \approx 100\%$.
2.  **Addition Node (Prerequisite)**:
    *   **Logic**: "User used Addition to solve Multiplication."
    *   **Action**: Internal review triggered `Rating.Good`.
    *   **FSRS Update**: $S$ increases from $10 \to 25$ days.
    *   **Result**: "Addition" review card is pushed 25 days into the future.

**Outcome**:
The system adapts. It knows you are practicing Addition *via* Multiplication, so it won't bug you with simple Addition flashcards.

## 4. Edge Cases & Safeguards

| Scenario | Logic | Safeguard |
| :--- | :--- | :--- |
| **Child Wrong** | Does failing Calculus mean I forgot Algebra? | **No**. It might be a new concept error. **Do not propagate failure** downwards. Only propagate successes. |
| **Too Frequent** | User does 10 Calculus Qs/day. Massive Algebra boost? | **Throttle**. Only trigger Prereq review if `today > P.last_review`. Prevent "over-stability". |
| **Decay** | User stops studying for a year. | All leaf $R$ values decay toward 0; any aggregated views should reflect the leaf decay. |
