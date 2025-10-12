from fastapi import FastAPI, Depends, status, HTTPException, Request
from contextlib import asynccontextmanager
from neo4j import AsyncGraphDatabase

from src.app.core.settings import settings
from src.app.core.database import engine, db_connections

from src.app.routes import auth, user, question
from src.app.routes import enrollment
# from src.app.routes import session
import src.app.models as models


# class DBConnections:
#     neo4j_driver = None
#
#
# db_connections = DBConnections()


# define lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Application starting up...")

    # Initialize the PostgreSQL
    async with engine.begin() as conn:
        print("Creating PostgreSQL tables ...")
        await conn.run_sync(models.Base.metadata.create_all)
        print("PostgreSQL tables created.")

    # Initialize Neo4j Driver
    print("Creating Neo4j driver ...")
    db_connections.neo4j_driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )
    await db_connections.neo4j_driver.verify_connectivity()

    app.state.db_connections = db_connections
    print("Neo4j driver created and connected")

    yield
    print("🌙 Application shutting down...")

    # Dispose PostgreSQL engine
    if engine:
        print("Closing PostgreSQL connection pool ...")
        await engine.dispose()
        print("PostgreSQL connection pool closed.")

    if db_connections.neo4j_driver:
        print("Closing Neo4j driver...")
        await db_connections.neo4j_driver.close()
        print("Neo4j driver closed.")


# pass lifespan tp FastAPI
app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(question.router)
app.include_router(enrollment.router)
# app.include_router(session.router)


@app.get("/health")
async def health_check(request: Request):
    try:
        driver = request.app.state.db_connections.neo4j_driver
        await driver.verify_connectivity()
        neo4j_status = "ok"
    except Exception as e:
        neo4j_status = f"error: {str(e)}"

    return {
        "message": "FastAPI + PostgreSQL run successfully",
        "neo4j_connection_status": neo4j_status
    }


@app.get("/")
async def root():
    return {"message": "FastAPI + PostgreSQL run successfully"}

app.state.db_connections = db_connections
