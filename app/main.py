from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models as models
from app.core.config import settings
from app.core.database import db_manager
from app.routes import question, user, quiz, submissions, admin, courses, knowledge_node


# define lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Application starting up...")

    await db_manager.initialize()
    await db_manager.create_all_tables(models.Base)
    print("✅ All databases initialized")

    yield
    print("🌙 Application shutting down...")

    await db_manager.close()
    print("✅ All databases closed")


# pass lifespan tp FastAPI
app = FastAPI(lifespan=lifespan)
app.include_router(user.router)
app.include_router(question.router)
# app.include_router(enrollment.router)
app.include_router(quiz.router)
app.include_router(submissions.router)
# app.include_router(courses.router)
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
