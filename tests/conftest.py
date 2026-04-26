import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Provide FastAPI TestClient"""
    return TestClient(app)


@pytest.fixture
def test_activities():
    """Provide a clean test activities database for each test"""
    return {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 2,
            "participants": ["michael@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 3,
            "participants": ["emma@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 2,
            "participants": []
        }
    }


@pytest.fixture
def client_with_test_db(client, test_activities, monkeypatch):
    """Provide TestClient with isolated test database"""
    # Patch the app's activities dictionary with test data
    monkeypatch.setattr("src.app.activities", test_activities)
    return client
