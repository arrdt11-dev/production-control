from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_dashboard_returns_200():
    response = client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 200

    data = response.json()
    assert "summary" in data
    assert "total_batches" in data["summary"]
    assert "active_batches" in data["summary"]
    assert "closed_batches" in data["summary"]
    assert "total_products" in data["summary"]
    assert "aggregated_products" in data["summary"]
    assert "aggregation_rate" in data["summary"]
