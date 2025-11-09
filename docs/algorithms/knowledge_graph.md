# Design Details of Knowledge Graph

## Node Types

1. **`(:KnowledgeNode)`** — Represents a knowledge point or concept.  
   **Properties:**
   - `node_id`: Unique identifier (use a `string` instead of a `UUID` for flexibility).
   - `node_name`: The name of the knowledge node.
   - `description`: A detailed description of the concept (useful for future LLM-based reasoning or content generation).

2. **`(:Question)`** — Represents an assessment item or problem linked to specific knowledge points.  
   **Properties:**
   - `question_id`: Unique identifier (`UUID`).
   - `text`: The main question text.
   - `details`: Additional metadata about the question — for example, multiple-choice options, correct answers, or explanations.
   - `difficulty`: The difficulty level of the question (e.g., `easy`, `medium`, `hard`, or a numeric scale).

---

## Relationships

### `IS_PREREQUISITE_FOR`

This is the **core relationship** that structures the knowledge graph.

- **Structure:**  
  `(:KnowledgeNode) -[r:IS_PREREQUISITE_FOR]-> (:KnowledgeNode)`
- **Meaning:**  
  Knowledge point **A** is a prerequisite for knowledge point **B**.
- **Attributes:**
  - **Basic model:**  
    The existence of this relationship alone defines the prerequisite structure — no attributes are required.
  - **Optional (advanced) attributes:**  
    - `importance` or `weight`: *(Float 0.0–1.0 or String)* — Indicates the strength or type of prerequisite relationship.
      - `importance: "critical"` — a strict prerequisite that must be fully mastered.
      - `importance: "supplementary"` — a supporting concept that’s helpful but not strictly required.  
      Alternatively, use numeric weights such as:
        - `weight: 1.0` → critical  
        - `weight: 0.7` → supplementary
    - **Note:** If this attribute is `null`, the algorithm should treat it as `"critical"` by default.  
      This ensures backward compatibility and simple graph traversal logic.

---

### `HAS_SUBTOPIC`

This relationship defines a **hierarchical decomposition** of a topic into its subtopics.

- **Structure:**  
  `(:KnowledgeNode) -[r:HAS_SUBTOPIC]-> (:KnowledgeNode)`
- **Meaning:**  
  Knowledge node **A** includes knowledge node **B** as one of its subtopics.
- **Attributes:**
  - `weight` or `relevance`: *(Float 0.0–1.0)* — Represents how much the subtopic contributes to its parent topic.  
    The weights of all subtopics for a parent node should sum to 1.0.
  - **Initialization rule:**  
    At early stages, if a topic has *n* subtopics, each can be assigned a default equal weight of `1/n`.  
    Later, subject matter experts can refine these weights for more precise modeling.

---

### `TEST`

This relationship connects **questions** to the **knowledge nodes** they assess.

- **Structure:**  
  `(:Question) -[r:TEST]-> (:KnowledgeNode)`
- **Meaning:**  
  Indicates that a specific question is used to test a given knowledge node.
- **Rules:**
  - A question should only be linked to **leaf knowledge nodes** (i.e., nodes that have no further subtopics).
  - This ensures that questions directly assess fundamental concepts, not aggregated topics.
- **Optional attributes (future extension):**
  - `weight`: *(Float 0.0–1.0)* — Represents how strongly this question assesses the target node (useful if one question covers multiple concepts).

- [ ] Consider how to apply the Bloom's Taxonomy in this model. or at least leave a hook. 
