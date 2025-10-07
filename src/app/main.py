from fastapi import FastAPI, Depends, status, HTTPException
from contextlib import asynccontextmanager

from src.app.core.database import get_db, engine
from src.app.models.base import Base
from src.app.routes import auth_router, user


# define lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


# pass lifespan tp FastAPI
app = FastAPI(lifespan=lifespan)

app.include_router(auth_router.router)
app.include_router(user.router)

@app.get("/")
async def root():
    return {"message": "FastAPI + PostgreSQL run successfully"}
