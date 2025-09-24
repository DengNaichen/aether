# "name": "Test Student",
#     "email": "test.student@example.com",
#     "password": "a-secure-password123"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from app.main import app
from sqlalchemy.orm import sessionmaker

from app.models import Base


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db" # Use the momory database for testing

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def test_db():
    Base. metadata.create_all(bind=engine)  # Create the tables
    yield
    Base.metadata.drop_all(bind=engine)  # Drop the tables after the test

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[app.get_db] = override_get_db
client = TestClient(app)

def test_registration_success():
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