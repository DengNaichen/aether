# Aether

**Adaptive learning backend built on knowledge graphs, FSRS mastery, and Gemini-powered ingestion.**

Aether pairs AI-generated knowledge graphs with a FSRS-first learning engine to deliver adaptive questions, mastery tracking, and spaced repetition.

## Highlights

- FSRS-first mastery engine with cached retrievability, implicit prerequisite boosts, and topology-aware question selection (no Neo4j/BKT dependency).
- Gemini-first ETL: Gemini 2.5 Flash (Files API) extracts PDFs to Markdown → Gemini 3 Pro builds/refines graphs → LangChain + Gemini generates questions for leaf nodes.
- Supabase/PostgreSQL data layer with Supabase JWT auth (provide `Authorization: Bearer <token>`; no local login endpoints).
- Graph APIs for creation, enrollment, visualization, imports, and an upload endpoint that turns PDFs/Markdown into graphs automatically.
- Cloud Run-ready Docker image and Makefile targets for build/deploy, plus CLI scripts for offline ingestion.

## Architecture & Stack

- **API:** FastAPI + SQLAlchemy on Python 3.12, packaged with `uv`.
- **Data:** Supabase/PostgreSQL (tables auto-created on startup); optional Redis for queues/tests.
- **AI:** google-genai (Gemini 2.5 Flash, Gemini 3 Pro), LangChain structured outputs, FSRS library.
- **Docs:** `docs/architecture.md`, `docs/fsrs_logic_design.md` outline data flow and mastery logic.

## Getting Started

Prerequisites: Docker, a reachable PostgreSQL/Supabase URL, Supabase JWT secret, and a Google API key for Gemini.

1) Copy env template and fill required values:

   ```bash
   cp .env.example .env.local
   ```

   Set at minimum: `ENVIRONMENT=local`, `DATABASE_URL`, `SUPABASE_JWT_SECRET`, `GOOGLE_API_KEY`. Optional: `REDIS_URL`, `EMAIL_FROM`, `RESEND_API_KEY`.

2) Run the API (no local DB container is started):

   ```bash
   docker-compose up          # or: make up / make down
   ```

   API docs: http://localhost:8000/docs • Health: http://localhost:8000/health

3) Local without Docker:

   ```bash
   ENVIRONMENT=local uv run uvicorn app.main:app --reload --port 8000
   ```

### Testing

- Start isolated test services (Postgres on 5433, Redis on 6380): `make test-up`
- Run tests with test env: `ENVIRONMENT=test uv run pytest` (or `make test` after exporting ENVIRONMENT)
- Stop test services: `make test-down`

## AI Ingestion Workflows

- **Upload API**: `POST /me/graphs/{graph_id}/upload-file` (PDF or Markdown) → Gemini 2.5 Flash extraction → Gemini 3 Pro graph generation/refinement → append-only persistence. Markdown snapshot saved under `temp/`.
- **CLI options**:
  - `uv run python scripts/extract_pdf.py path/to/file.pdf -o out.md`
  - `uv run python scripts/generate_graph_from_md.py out.md --graph-id <uuid>`
  - `uv run python scripts/generate_questions_for_graph.py <graph_id> --count 3`
- Graph generation is append-only and deduplicates by `node_id_str`; invalid prerequisite edges are corrected via LLM refinement (`app/services/ai_services/generate_graph.py`).

## Learning Engine

- FSRS stores stability, difficulty, due dates, review logs, and cached retrievability in `user_mastery`; mastery is tracked per leaf node (parent aggregation has been removed).
- Correct answers probabilistically trigger implicit prerequisite reviews (depth decay) to reward transfer (see `docs/fsrs_logic_design.md`).
- Question selection: FSRS due filter → topology/urgency sorting → stability-based new learning fallback (`app/services/question_rec.py`).

## API Surface (Bearer tokens from Supabase Auth)

- Users: `GET /users/me`
- My graphs: `GET/POST /me/graphs`, `GET /me/graphs/{id}`, `POST /me/graphs/{id}/enrollments`, `POST /me/graphs/{id}/nodes|prerequisites|questions`, `POST /me/graphs/{id}/upload-file`, `GET /me/graphs/{id}/next-question|visualization|content`
- Public graphs: `GET /graphs/templates`, `POST /graphs/{id}/enrollments`, `GET /graphs/{id}/next-question|visualization|content`
- Learning: `POST /answer` for single-answer grading + mastery update

## Deployment

- Cloud Run ready: `make deploy-all` or `make gcp-build` + `make gcp-deploy` (uses `env.yaml`).
- Full steps/checklists: `docs/deployment.md`, `docs/deployment-checklist.md`.

## Roadmap

Progress and upcoming milestones are tracked in `docs/roadmap.md`.

## License

MIT
