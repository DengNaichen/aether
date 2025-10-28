# Mastery Level Propagation Algorithm
Refer to sign node [mastery level](./mastery_level_kbt.md)), assume the student name is Chloe.
## Step 1: Initial Answer Processing

This is the first step that runs immediately upon answer submission.

1. **Submission:** Chloe answers `Question_Q`.
2. **Find Leaf Node:** The system finds the `KnowledgeNode_L` linked via `(Question_Q) -[:TESTS]-> (KnowledgeNode_L)`.
3. **Apply BKT:**
    - Get $P(L_{t-1})$ (current mastery) from `Node_L`.
    - Get $P(G)$, $P(S)$, and $P(T)$ (from the question or node defaults).
    - Calculate the new $P(L_t)_{\text{final}}$ using the appropriate BKT update formulas (i.e., the "Correct" or "Incorrect" formula followed by the "Incorporating Learning" formula).
4. **Save Update:** Save this new $P(L_t)_{\text{final}}$ mastery score to `Node_L`.

---

## Step 2: Trigger Propagation

After `Node_L`'s score is updated, the system triggers two *different* propagation types simultaneously.

### Propagation Type 1: `HAS_SUBTOPIC` (Bottom-Up Aggregation)

This update recalculates the mastery of parent *topics* based on their component parts.

1. **Find Parent:** Find the parent `Node_P` where `(Node_L) <-[r:HAS_SUBTOPIC]- (Node_P)`.
2. **Trigger Recalculation:** If `Node_P` exists, trigger a recalculation of its mastery score.
3. **Calculation:** The mastery of `Node_P` is the **weighted sum** of *all* its subtopics' current masteries.
$$
\text{Mastery}(P) = \sum_{i} \left( \text{Mastery}(S_i) \cdot \text{weight}(r_i) \right)
$$
(Where $S_i$ is a subtopic and $r_i$ is its relationship to $P$).
4. **Recurse:** This process is recursive. If `Node_P`'s score changes, it triggers a recalculation for *its* parent, continuing all the way up the `HAS_SUBTOPIC` hierarchy.

### Propagation Type 2: `IS_PREREQUISITE_FOR` (Logical Inference)

This update propagates inferences about dependent skills.

**A. Backward Propagation (Inferring prerequisite mastery)**

- **If the answer to `Question_Q` was CORRECT:**
    - **Inference:** Chloe likely understood and used the prerequisite skills correctly.
    - **Algorithm:**
        1. Find all prerequisite nodes `Node_A` where `(Node_A) -[:IS_PREREQUISITE_FOR]-> (Node_L)`.
        2. For each `Node_A`, apply the **BKT "Correct" update** and the **Learning update** *as if* Chloe had just answered a question for `Node_A` correctly.
        3. This acts as a "bonus" update, strengthening the belief in their prerequisite knowledge.
- **If the answer to `Question_Q` was INCORRECT:**
    - **Inference:** The cause is ambiguous. It could be a failure of `Node_L` or its prerequisite `Node_A`.
    - **Algorithm:**
        1. **DO NOT** propagate the failure backward. The mastery score of `Node_A` is *not* changed.
        2. **Action:** Flag `Node_A` for the **recommendation engine**. The system's next move should be to test `Node_A` directly to resolve the ambiguity.

**B. Forward Propagation (Updating future readiness)**

- **Inference:** Mastering a prerequisite (`Node_L`) means Chloe is now prepared to learn the post-requisite (`Node_B`).
- **Algorithm:**
    1. Find all post-requisite nodes `Node_B` where `(Node_L) -[:IS_PREREQUISITE_FOR]-> (Node_B)`.
    2. Recalculate the **Prior Knowledge** parameter ($P(L_0)$) for `Node_B`.
    3. This calculation should be based on the mastery of *all* of B's prerequisites. A simple, robust model is to use the *minimum* mastery of all its required prerequisites.

    $$
    P(L_0)_{\text{Node\_B}} = \text{MIN}(\text{Mastery of all prerequisites of B})
    $$
    4. **Result:** The next time the Chloe sees a question for `Node_B`, the BKT calculation will start from this higher, more accurate $P(L_0)$, allowing for faster mastery.