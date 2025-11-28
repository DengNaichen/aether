from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models as models
from app.core.config import settings
from app.core.database import db_manager
from app.routes import question, user, admin, knowledge_node, knowledge_graph, answer
from fastapi.middleware.cors import CORSMiddleware


# define lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Application starting up...")
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
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://learning-project-fronted.vercel.app",  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(user.router)
app.include_router(question.router)
app.include_router(admin.router)
app.include_router(knowledge_node.router)
app.include_router(knowledge_graph.router)
app.include_router(knowledge_graph.public_router)  # Public endpoints for graphs
app.include_router(answer.router)


@app.get("/health")
async def health_check():
    return {
        "message": "FastAPI + PostgreSQL + Neo4j run successfully",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
async def root():
    return {"message": "FastAPI + PostgreSQL run successfully"}
