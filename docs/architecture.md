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
        BKT["BKT Engine<br/>(Bayesian Knowledge Tracing)"]
        FSRS["FSRS Scheduler<br/>(Spaced Repetition)"]
        GraphGen["Graph Generator<br/>(LangChain + Agent)"]
        RecEngine["Recommendation Engine<br/>(Hybrid BKT + FSRS)"]
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
    RecEngine -->|Get Mastery State| BKT
    RecEngine -->|Get Schedule| FSRS
    
    MasteryAPI --> BKT
    MasteryAPI --> FSRS

    %% Database Connections
    Auth --> Postgres
    GraphAPI --> Postgres
    MasteryAPI --> Postgres
    BKT -.->|Read/Write State| Postgres
    FSRS -.->|Read/Write Logs| Postgres

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
    *   **FSRS** filters for due reviews.
    *   **BKT** prioritizes based on prerequisite chains and probability scores.
    *   Optimal question is returned.

2.  **AI Content Generation**:
    *   User uploads a PDF or topic request.
    *   **Graph Generator** uses **LangChain** to construct a prompt.
    *   **Gemini Pro** extracts concepts and relationships.
    *   **Self-Correction Agent** verifies graph topology (DAG structure) before saving to DB.
