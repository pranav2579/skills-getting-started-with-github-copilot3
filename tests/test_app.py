"""
Tests for the Mergington High School Activities API.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to their original state before each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# ── GET / ───────────────────────────────────────────────────────────────────

class TestRoot:
    def test_root_redirects_to_index(self, client):
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


# ── GET /activities ─────────────────────────────────────────────────────────

class TestGetActivities:
    def test_get_activities_returns_all(self, client):
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == len(activities)

    def test_get_activities_contains_expected_keys(self, client):
        response = client.get("/activities")
        data = response.json()
        for name, details in data.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details

    def test_get_activities_has_known_activity(self, client):
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data
        assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"


# ── POST /activities/{name}/signup ──────────────────────────────────────────

class TestSignup:
    def test_signup_success(self, client):
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant(self, client):
        email = "teststudent@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert email in participants

    def test_signup_activity_not_found(self, client):
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_email(self, client):
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up"

    def test_signup_missing_email(self, client):
        response = client.post("/activities/Chess Club/signup")
        assert response.status_code == 422

    def test_signup_multiple_activities(self, client):
        email = "multi@mergington.edu"
        r1 = client.post(f"/activities/Chess Club/signup?email={email}")
        r2 = client.post(f"/activities/Art Club/signup?email={email}")
        assert r1.status_code == 200
        assert r2.status_code == 200

        data = client.get("/activities").json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Art Club"]["participants"]
