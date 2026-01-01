# Aether Roadmap (High-Level)

Vision: adaptive learning with AI-generated knowledge graphs + FSRS mastery. Timelines intentionally omitted; focus is on priorities and readiness signals.

## Status Snapshot

- Backend: FastAPI + PostgreSQL + FSRS mastery, Supabase JWT auth, graph CRUD, questions (MC/fill/calculation), adaptive recommendation, PDF/MD → graph/question pipeline (Gemini 2.5 Flash + Gemini 3 Pro).
- Frontend: Auth, graph viz, quiz UI, notes; deployed on Vercel.
- DevOps: Docker, Cloud Run path, lint/test CI (pytest).
- Pain points: onboarding, discovery, AI-assisted UI, social features, coverage gaps.

## Current Focus (Do Next)

- Graph RAG (incremental + QA): incremental ingest of new docs into existing graphs (dedupe/merge), vector index over nodes/chunks, and graph-aware QA endpoint that cites nodes/edges.
- Frontend polish: onboarding, discovery/search, dashboard for daily reviews/overdue, mobile-friendly graph UX.
- AI-assisted creation: PDF upload + text-to-graph in UI, preview/edit before save, batch question generation; async tasks + progress updates (SSE/WebSocket).
- Reliability: raise test coverage on recommendation, grading/mastery update, graph enrollment; reduce N+1 in graph traversal; better error UX.

## Near-Term Growth

- Social/discovery: categories/tags, trending/recommended graphs, simple forking/remix, basic feedback/reporting on questions.
- Analytics: user learning progress (over time + streaks), creator analytics (enrollment, difficulty distribution, drop-off points).
- Interop: export to Anki/Markdown; import from Anki (lightweight path).

## Platform & Ops

- Monitoring/observability: structured logs, request IDs, error tracking, basic APM; stable health checks.
- Background jobs: queue for PDF/graph/question generation; daily FSRS recalcs optional.
- Security & hardening: rate limiting, CORS correctness, dependency hygiene.

## Success Signals

- Learner: completes onboarding → enrolls → answers 10+ questions with stable FSRS schedule; overdue count drops after a session.
- Creator: uploads/edits a PDF or markdown, reviews preview, saves graph/questions without manual DB work.
- Quality: p95 question-recommend latency within target; failing tests blocked in CI; no silent task failures in pipelines.
