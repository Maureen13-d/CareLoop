def move(client, headers, case_id, to_state, note=None):
    return client.post(
        f"/api/v1/cases/{case_id}/transitions",
        json={"to_state": to_state, "note": note},
        headers=headers,
    )


def test_valid_transition_resets_owner_and_deadline(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    resp = move(client, auth["coord"], cid, "PATIENT_NOTIFIED")
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "PATIENT_NOTIFIED"
    assert body["owner_department"] == "Care coordination"
    assert body["unowned"] is True


def test_skipping_a_stage_is_rejected(client, auth, make_case):
    _, r = make_case()
    resp = move(client, auth["clin"], r["case_id"], "TREATMENT_STARTED")
    assert resp.status_code == 409
    err = resp.json()["error"]
    assert err["code"] == "invalid_transition"
    assert err["details"]["allowed_next"] == ["PATIENT_NOTIFIED"]


def test_unknown_state_is_rejected(client, auth, make_case):
    _, r = make_case()
    assert move(client, auth["clin"], r["case_id"], "NOT_A_STATE").status_code == 422


def test_cannot_end_case_through_transitions(client, auth, make_case):
    _, r = make_case()
    assert move(client, auth["clin"], r["case_id"], "CLOSED").status_code == 409


def test_coordinator_cannot_enter_clinician_only_stage(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    for state in ("PATIENT_NOTIFIED", "PATIENT_ACKNOWLEDGED", "CONFIRMATION_SCHEDULED"):
        assert move(client, auth["coord"], cid, state).status_code == 200
    resp = move(client, auth["coord"], cid, "CONFIRMATION_COMPLETED")
    assert resp.status_code == 403
    assert move(client, auth["clin"], cid, "CONFIRMATION_COMPLETED").status_code == 200


def walk_to(client, auth, cid, states):
    for state in states:
        who = "clin"
        assert move(client, auth[who], cid, state).status_code == 200, state


def test_cannot_close_without_evidence(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    walk_to(
        client,
        auth,
        cid,
        [
            "PATIENT_NOTIFIED",
            "PATIENT_ACKNOWLEDGED",
            "CONFIRMATION_SCHEDULED",
            "CONFIRMATION_COMPLETED",
        ],
    )
    resp = client.post(f"/api/v1/cases/{cid}/close", json={}, headers=auth["clin"])
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "evidence_required"


def test_cannot_close_from_early_stage_even_with_evidence(client, auth, make_case):
    _, r = make_case()
    resp = client.post(
        f"/api/v1/cases/{r['case_id']}/close",
        json={"evidence_type": "clinician_decision", "description": "x"},
        headers=auth["clin"],
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "invalid_transition"


def test_close_with_evidence_in_the_same_call(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    walk_to(
        client,
        auth,
        cid,
        [
            "PATIENT_NOTIFIED",
            "PATIENT_ACKNOWLEDGED",
            "CONFIRMATION_SCHEDULED",
            "CONFIRMATION_COMPLETED",
        ],
    )
    resp = client.post(
        f"/api/v1/cases/{cid}/close",
        json={
            "evidence_type": "confirmed_negative",
            "description": "Synthetic: confirmatory result negative",
        },
        headers=auth["clin"],
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "CLOSED"
    assert body["closure_reason"] == "confirmed_negative"
    assert body["deadline_at"] is None
    assert (
        move(client, auth["clin"], cid, "PATIENT_NOTIFIED").status_code == 409
    )  # closed cases stay closed


def test_close_with_previously_attached_evidence(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    walk_to(
        client,
        auth,
        cid,
        [
            "PATIENT_NOTIFIED",
            "PATIENT_ACKNOWLEDGED",
            "CONFIRMATION_SCHEDULED",
            "CONFIRMATION_COMPLETED",
        ],
    )
    ev = client.post(
        f"/api/v1/cases/{cid}/evidence",
        json={"type": "confirmed_negative", "description": "Synthetic"},
        headers=auth["coord"],
    )
    assert ev.status_code == 201
    assert (
        client.post(f"/api/v1/cases/{cid}/close", json={}, headers=auth["clin"]).status_code == 200
    )


def test_coordinator_cannot_close(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    walk_to(
        client,
        auth,
        cid,
        [
            "PATIENT_NOTIFIED",
            "PATIENT_ACKNOWLEDGED",
            "CONFIRMATION_SCHEDULED",
            "CONFIRMATION_COMPLETED",
        ],
    )
    resp = client.post(
        f"/api/v1/cases/{cid}/close",
        json={"evidence_type": "confirmed_negative", "description": "x"},
        headers=auth["coord"],
    )
    assert resp.status_code == 403


def test_bad_evidence_type_is_rejected(client, auth, make_case):
    _, r = make_case()
    resp = client.post(
        f"/api/v1/cases/{r['case_id']}/evidence",
        json={"type": "vibes", "description": "x"},
        headers=auth["clin"],
    )
    assert resp.status_code == 422


def test_timeline_records_every_move_in_order(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    move(client, auth["coord"], cid, "PATIENT_NOTIFIED", "message approved")
    events = client.get(f"/api/v1/cases/{cid}/timeline", headers=auth["coord"]).json()
    assert [e["to_state"] for e in events] == ["OPENED", "PATIENT_NOTIFIED"]
    assert events[1]["note"] == "message approved"
    assert events[1]["actor_name"] == "Coord"


def test_claim_makes_case_owned(client, auth, make_case):
    _, r = make_case()
    resp = client.post(f"/api/v1/cases/{r['case_id']}/claim", headers=auth["coord"])
    assert resp.json()["unowned"] is False
    assert resp.json()["owner_user_name"] == "Coord"
    unowned = client.get("/api/v1/cases?unowned=true", headers=auth["coord"]).json()
    assert unowned == []


def test_state_changes_and_refusals_are_audited(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    move(client, auth["coord"], cid, "PATIENT_NOTIFIED")
    move(client, auth["clin"], cid, "TREATMENT_STARTED")  # invalid, refused
    entries = client.get(
        "/api/v1/audit?entity_type=care_case&limit=100", headers=auth["admin"]
    ).json()
    actions = [(e["action"], e["outcome"]) for e in entries]
    assert ("case.open", "success") in actions
    assert ("case.transition", "success") in actions
    assert ("case.transition", "rejected") in actions
