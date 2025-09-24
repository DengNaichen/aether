import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.main import app
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.database import get_db


SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db" # Use the momory database for testing

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db



@pytest_asyncio.fixture(scope="function")
async def test_db():
    # Create the database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    # Drop the database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


client = TestClient(app)

@pytest.mark.asyncio

async def test_registration_success(test_db):
    # a successful registration student data
    new_student = {
        "name": "Test Student",
        "email": "test.student@example.com",
        "password": "a-secure-password123"
    }

    # send post request 
    response = client.post("/register", json=new_student)

    # assert status code
    assert response.status_code == 201
    # assert return data
    response_data = response.json()

    # verify id
    assert "id" in response_data

    # verify create at
    assert "created_at" in response_data
    # verufy it is not None and is a string
    assert isinstance(response_data["created_at"], str)

    # verify other fields
    assert response_data["name"] == new_student["name"]
    assert response_data["email"] == new_student["email"]
    
    assert "password" not in response_data  # Ensure password is not returned