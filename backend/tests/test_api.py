def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_cases_requires_auth(client):
    assert client.get("/api/v1/cases").status_code == 401
