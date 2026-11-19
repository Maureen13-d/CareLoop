def test_health_is_public(client):
    assert client.get("/api/v1/health").json()["synthetic_data_only"] is True


def test_cases_need_login(client):
    resp = client.get("/api/v1/cases")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "not_authenticated"


def test_wrong_password_is_rejected(client):
    resp = client.post("/api/v1/auth/login", data={"username": "coord", "password": "nope"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_credentials"


def test_program_manager_cannot_see_cases(client, auth):
    assert client.get("/api/v1/cases", headers=auth["manager"]).status_code == 403


def test_only_admin_and_manager_read_audit(client, auth):
    assert client.get("/api/v1/audit", headers=auth["nav"]).status_code == 403
    assert client.get("/api/v1/audit", headers=auth["manager"]).status_code == 200
    assert client.get("/api/v1/audit", headers=auth["admin"]).status_code == 200


def test_denied_access_is_audited(client, auth):
    client.get("/api/v1/audit", headers=auth["nav"])  # denied
    entries = client.get("/api/v1/audit?outcome=denied", headers=auth["admin"]).json()
    assert any(e["action"] == "access.denied" for e in entries)


def test_demo_controls_are_admin_only(client, auth):
    assert (
        client.post(
            "/api/v1/admin/advance-clock", json={"hours": 1}, headers=auth["clin"]
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/admin/advance-clock", json={"hours": 1}, headers=auth["admin"]
        ).status_code
        == 200
    )
