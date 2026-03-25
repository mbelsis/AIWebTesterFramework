"""
Tests for the mock demo application endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from mock_app.app import app, EMPLOYEES, SESSION_COOKIE


@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state between tests."""
    import mock_app.app as mod
    mod.EMPLOYEES.clear()
    mod.NEXT_ID = 1
    yield
    mod.EMPLOYEES.clear()
    mod.NEXT_ID = 1


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def logged_in_client(client):
    """Client with an active session cookie."""
    resp = client.post("/login", data={"username": "test", "password": "test"})
    assert resp.status_code == 200  # follows redirect
    return client


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["total_employees"] == 0

    def test_health_reflects_employee_count(self, logged_in_client):
        logged_in_client.post("/employees", data={
            "first_name": "A", "last_name": "B", "email": "a@b.com", "role": "dev"
        })
        resp = logged_in_client.get("/health")
        assert resp.json()["total_employees"] == 1


class TestLoginFlow:
    def test_root_redirects_to_login(self, client):
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code == 307 or resp.status_code == 302
        assert "/login" in resp.headers.get("location", "")

    def test_login_page_renders(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200
        assert "login" in resp.text.lower()

    def test_login_post_sets_cookie_and_redirects(self, client):
        resp = client.post(
            "/login",
            data={"username": "admin", "password": "pass"},
            follow_redirects=False
        )
        assert resp.status_code == 303
        assert "/employees/new" in resp.headers.get("location", "")
        assert SESSION_COOKIE in resp.cookies

    def test_employees_new_requires_auth(self, client):
        resp = client.get("/employees/new", follow_redirects=False)
        # Should redirect to login
        assert resp.status_code in (302, 307)

    def test_employees_new_accessible_after_login(self, logged_in_client):
        resp = logged_in_client.get("/employees/new")
        assert resp.status_code == 200


class TestEmployeeCRUD:
    def test_create_employee(self, logged_in_client):
        resp = logged_in_client.post("/employees", data={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "role": "Engineer"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "John Doe" in data["message"]
        assert data["employee_id"] == 1

    def test_create_multiple_employees(self, logged_in_client):
        for i in range(3):
            resp = logged_in_client.post("/employees", data={
                "first_name": f"User{i}",
                "last_name": "Test",
                "email": f"user{i}@test.com",
                "role": "Tester"
            })
            assert resp.json()["employee_id"] == i + 1

    def test_list_employees(self, logged_in_client):
        logged_in_client.post("/employees", data={
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@test.com",
            "role": "QA"
        })
        resp = logged_in_client.get("/api/employees")
        assert resp.status_code == 200
        employees = resp.json()["employees"]
        assert len(employees) == 1
        assert employees[0]["first_name"] == "Jane"
        assert employees[0]["email"] == "jane@test.com"

    def test_list_employees_empty(self, client):
        resp = client.get("/api/employees")
        assert resp.status_code == 200
        assert resp.json()["employees"] == []
