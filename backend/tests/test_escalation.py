def advance(client, auth, hours):
    assert client.post("/api/v1/admin/advance-clock", json={"hours": hours}, headers=auth["admin"]).status_code == 200


def run_check(client, auth):
    resp = client.post("/api/v1/admin/run-deadline-check", headers=auth["admin"])
    assert resp.status_code == 200
    return resp.json()["escalations_created"]


def test_no_escalation_before_deadline(client, auth, make_case):
    make_case()
    advance(client, auth, 47)  # OPENED allows 48 hours
    assert run_check(client, auth) == 0


def test_level_1_after_deadline_and_check_is_idempotent(client, auth, make_case):
    _, r = make_case()
    advance(client, auth, 49)
    assert run_check(client, auth) == 1
    assert run_check(client, auth) == 0
    esc = client.get("/api/v1/escalations", headers=auth["coord"]).json()
    assert len(esc) == 1 and esc[0]["level"] == 1 and esc[0]["case_id"] == r["case_id"]
    case = client.get(f"/api/v1/cases/{r['case_id']}", headers=auth["coord"]).json()
    assert case["overdue"] is True
    assert case["open_escalations"] == 1


def test_level_2_when_still_overdue_after_grace(client, auth, make_case):
    make_case()
    advance(client, auth, 49)
    run_check(client, auth)
    advance(client, auth, 49)  # now 49h past the deadline (grace is 48h)
    assert run_check(client, auth) == 1
    levels = sorted(e["level"] for e in client.get("/api/v1/escalations", headers=auth["coord"]).json())
    assert levels == [1, 2]


def test_late_first_check_creates_both_levels(client, auth, make_case):
    make_case()
    advance(client, auth, 48 + 50)
    assert run_check(client, auth) == 2


def test_urgent_case_starts_at_level_2(client, auth, make_case):
    make_case("suspected_cancer")
    advance(client, auth, 49)
    assert run_check(client, auth) == 1
    esc = client.get("/api/v1/escalations", headers=auth["coord"]).json()
    assert [e["level"] for e in esc] == [2]


def test_moving_forward_gives_a_fresh_deadline(client, auth, make_case):
    _, r = make_case()
    advance(client, auth, 49)
    run_check(client, auth)
    client.post(f"/api/v1/cases/{r['case_id']}/transitions", json={"to_state": "PATIENT_NOTIFIED"}, headers=auth["coord"])
    case = client.get(f"/api/v1/cases/{r['case_id']}", headers=auth["coord"]).json()
    assert case["overdue"] is False
    assert run_check(client, auth) == 0


def test_resolving_an_escalation(client, auth, make_case):
    make_case()
    advance(client, auth, 49)
    run_check(client, auth)
    esc_id = client.get("/api/v1/escalations", headers=auth["coord"]).json()[0]["id"]
    resp = client.post(f"/api/v1/escalations/{esc_id}/resolve", json={"note": "Called the clinic"}, headers=auth["coord"])
    assert resp.status_code == 200 and resp.json()["resolved_at"]
    assert client.get("/api/v1/escalations", headers=auth["coord"]).json() == []
    assert client.post(f"/api/v1/escalations/{esc_id}/resolve", json={"note": "again"}, headers=auth["coord"]).status_code == 409
    assert run_check(client, auth) == 0  # a resolved level is not re-raised


def test_lost_to_follow_up_needs_escalation_and_a_note(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    resp = client.post(f"/api/v1/cases/{cid}/mark-lost", json={"note": "Cannot reach patient"}, headers=auth["coord"])
    assert resp.status_code == 409 and resp.json()["error"]["code"] == "escalation_required"
    advance(client, auth, 49)
    run_check(client, auth)
    assert client.post(f"/api/v1/cases/{cid}/mark-lost", json={"note": ""}, headers=auth["coord"]).status_code == 422
    resp = client.post(f"/api/v1/cases/{cid}/mark-lost", json={"note": "Cannot reach patient after 3 attempts"}, headers=auth["coord"])
    assert resp.status_code == 200 and resp.json()["state"] == "LOST_TO_FOLLOW_UP"
    assert client.get("/api/v1/cases", headers=auth["coord"]).json() == []  # closed cases leave the open worklist
    closed = client.get("/api/v1/cases?status=closed", headers=auth["coord"]).json()
    assert len(closed) == 1
