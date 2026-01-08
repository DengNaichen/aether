# System Architecture

```mermaid
graph TD
    %% Client Layer
    subgraph Client ["Client Layer"]
        WebApp["Web App (Next.js + React)"]
        Mobile["Mobile App (Planned)"]
    end

    %% API Layer
    subgraph API ["API Layer (FastAPI)"]
        Auth["Auth Router"]
        GraphAPI["Knowledge Graph Router"]
        QuestionAPI["Question Router"]
        MasteryAPI["Mastery Router"]
    end

    %% Service Layer
    subgraph Services ["Business Logic Services"]
        FSRS["FSRS Scheduler<br/>(Spaced Repetition)"]
        GraphGen["Graph Generator<br/>(LangChain + Agent)"]
        RecEngine["Recommendation Engine<br/>(FSRS + Topology)"]
    end

    %% AI Layer
    subgraph AI ["AI / LLM Layer"]
        Gemini["Google Gemini Pro"]
        LangChain["LangChain Orchestrator"]
    end

    %% Data Layer
    subgraph Data ["Data Persistence"]
        Postgres[("PostgreSQL 15")]
    end

    %% Connections
    WebApp -->|REST / JWT| Auth
    WebApp -->|REST| GraphAPI
    WebApp -->|REST| QuestionAPI
    WebApp -->|REST| MasteryAPI

    GraphAPI --> GraphGen
    GraphGen -->|Prompt Engineering| LangChain
    LangChain -->|API Call| Gemini

    QuestionAPI --> RecEngine
    RecEngine -->|Get Schedule + Mastery| FSRS

    MasteryAPI --> FSRS

    %% Database Connections
    Auth --> Postgres
    GraphAPI --> Postgres
    MasteryAPI --> Postgres
    FSRS -.->|Read/Write State| Postgres

    %% Styling
    classDef client fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef api fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef service fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px;
    classDef ai fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef data fill:#eceff1,stroke:#263238,stroke-width:2px;

    class WebApp,Mobile client;
    class Auth,GraphAPI,QuestionAPI,MasteryAPI api;
    class BKT,FSRS,GraphGen,RecEngine service;
    class Gemini,LangChain ai;
    class Postgres data;
```

## Data Flow Description

1.  **Adaptive Learning Loop**:
    *   User requests a question via **Web App**.
    *   **Recommendation Engine** queries **PostgreSQL** for current mastery state.
    *   **FSRS** filters for due reviews and supplies stability/retrievability.
    *   **RecEngine** sorts by prerequisites/topology, urgency, and mastery gap.
    *   Optimal question is returned.

2.  **AI Content Generation**:
    *   User uploads a PDF.
    *   **PDF Extractor** uses **Gemini 2.5 Flash** (Files API) for multimodal text extraction.
    *   **Graph Generator** uses **Gemini 3 Pro** to extract knowledge nodes and relationships.
    *   **Refinement Agent** validates and corrects graph topology (e.g., re-routing parent dependencies).
    *   **Question Generator** creates adaptive questions for leaf nodes.

## Core Data Model (ERD)

```mermaid
erDiagram
    USERS ||--o{ KNOWLEDGE_GRAPHS : owns
    USERS ||--o{ GRAPH_ENROLLMENTS : enrolls
    KNOWLEDGE_GRAPHS ||--o{ GRAPH_ENROLLMENTS : "has learners"
    KNOWLEDGE_GRAPHS ||--o{ KNOWLEDGE_NODES : contains
    KNOWLEDGE_NODES ||--o{ PREREQUISITES : "from_node_id"
    KNOWLEDGE_NODES ||--o{ PREREQUISITES : "to_node_id"
    KNOWLEDGE_NODES ||--o{ QUESTIONS : assesses
    USERS ||--o{ USER_MASTERY : "per graph/node"
    KNOWLEDGE_NODES ||--o{ USER_MASTERY : tracked

    USERS {
        UUID id
        string email
    }
    KNOWLEDGE_GRAPHS {
        UUID id
        UUID owner_id
        string name
        bool is_public
        bool is_template
    }
    GRAPH_ENROLLMENTS {
        UUID id
        UUID user_id
        UUID graph_id
        bool is_active
    }
    KNOWLEDGE_NODES {
        UUID id
        UUID graph_id
        string node_id_str
        string node_name
        int level
    }
    PREREQUISITES {
        UUID graph_id
        UUID from_node_id
        UUID to_node_id
        float weight
    }
    QUESTIONS {
        UUID id
        UUID graph_id
        UUID node_id
        string question_type
        string difficulty
        jsonb details
    }
    USER_MASTERY {
        UUID user_id
        UUID graph_id
        UUID node_id
        float cached_retrievability
        float fsrs_stability
        float fsrs_difficulty
        timestamptz due_date
        jsonb review_log
    }
```

- `USER_MASTERY` is the FSRS store keyed by `(user_id, graph_id, node_id)`; only leaf nodes are tracked, no parent aggregation.
- `PREREQUISITES` and `QUESTIONS` are leaf-only; subtopic hierarchy is not persisted separately.
- `GRAPH_ENROLLMENTS` tracks who is learning a graph; owners are in `KNOWLEDGE_GRAPHS.owner_id`.
