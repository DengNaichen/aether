from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

import app.models as models
from app.core.config import settings
from app.core.database import db_manager
from app.routes import question, user, quiz, submissions, admin, courses, knowledge_node
from fastapi.middleware.cors import CORSMiddleware


class DebugAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log Authorization header for debugging
        auth_header = request.headers.get("Authorization", "NOT FOUND")
        print(f"🔍 [Middleware] {request.method} {request.url.path} - Auth header: {auth_header[:50] if len(auth_header) > 50 else auth_header}...")
        response = await call_next(request)
        print(f"📤 [Middleware] Response status: {response.status_code}")
        return response


# define lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Application starting up...")

    # Initialize neomodel configuration for synchronous queries
    from neomodel import config as neomodel_config
    neomodel_config.DATABASE_URL = settings.NEOMODEL_NEO4J_URI
    print(f"🔧 Neomodel configured with URI: {settings.NEO4J_URI}")

    # Try to initialize databases, but don't fail if they're not available
    try:
        await db_manager.initialize()
        await db_manager.create_all_tables(models.Base)
        print("✅ All databases initialized")
    except Exception as e:
        print(f"⚠️  Warning: Database initialization failed: {e}")
        print("⚠️  Application will start anyway (database endpoints may not work)")

    yield
    print("🌙 Application shutting down...")

    try:
        await db_manager.close()
        print("✅ All databases closed")
    except Exception as e:
        print(f"⚠️  Warning: Database close failed: {e}")


# pass lifespan tp FastAPI
app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add debug middleware
app.add_middleware(DebugAuthMiddleware)

app.include_router(user.router)
app.include_router(question.router)
# app.include_router(enrollment.router)
app.include_router(quiz.router)
app.include_router(submissions.router)
app.include_router(courses.router)
app.include_router(admin.router)
app.include_router(courses.router)
app.include_router(knowledge_node.router)


@app.get("/health")
async def health_check():
    neo4j_status = "ok"
    try:
        await db_manager.neo4j_driver.verify_connectivity()

    except Exception as e:
        neo4j_status = f"error: {str(e)}"

    return {
        "message": "FastAPI + PostgreSQL + Neo4j run successfully",
        "neo4j_connection_status": neo4j_status,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
async def root():
    return {"message": "FastAPI + PostgreSQL run successfully"}
