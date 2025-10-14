from fastapi import FastAPI, Depends, status, HTTPException, Request
from contextlib import asynccontextmanager
from neo4j import AsyncGraphDatabase

from src.app.routes import quiz
from src.app.core.config import settings
from src.app.core.database import db_manager

from src.app.routes import auth, user, question, course, submissions
import src.app.models as models


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
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(question.router)
app.include_router(course.router)
app.include_router(quiz.router)
app.include_router(submissions.router)


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
