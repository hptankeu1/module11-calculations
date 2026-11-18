from fastapi.testclient import TestClient

from app.main import app


def test_health_and_types(db_engine):
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200 and r.json()["database"] == "connected"
        assert client.get("/calculation-types").json() == ["Add", "Sub", "Multiply", "Divide"]
