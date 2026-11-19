def move(client, headers, case_id, to_state, note=None):
    return client.post(
        f"/api/v1/cases/{case_id}/transitions",
        json={"to_state": to_state, "note": note},
        headers=headers,
    )


TO_ARRIVAL = [
    "PATIENT_ENGAGED",
    "BARRIERS_ASSESSED",
    "NAVIGATION_ACTIVE",
    "APPOINTMENT_BOOKED",
    "ARRIVAL_CONFIRMED",
]
TO_HANDOFF = TO_ARRIVAL + ["HANDED_OFF"]


def walk(client, auth, cid, states):
    for state in states:
        assert move(client, auth["clin"], cid, state).status_code == 200, state


def test_valid_transition_resets_owner_and_deadline(client, auth, make_case):
    _, r = make_case()
    resp = move(client, auth["nav"], r["case_id"], "PATIENT_ENGAGED")
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "PATIENT_ENGAGED"
    assert body["owner_department"] == "Navigation team"
    assert body["unowned"] is True


def test_skipping_a_stage_is_rejected(client, auth, make_case):
    _, r = make_case()
    resp = move(client, auth["clin"], r["case_id"], "APPOINTMENT_BOOKED")
    assert resp.status_code == 409
    err = resp.json()["error"]
    assert err["code"] == "invalid_transition"
    assert err["details"]["allowed_next"] == ["PATIENT_ENGAGED"]


def test_unknown_state_is_rejected(client, auth, make_case):
    _, r = make_case()
    assert move(client, auth["clin"], r["case_id"], "NOT_A_STATE").status_code == 422


def test_cannot_end_case_through_transitions(client, auth, make_case):
    _, r = make_case()
    for ending in ("CLOSED", "PATIENT_DECLINED", "LOST_TO_FOLLOW_UP"):
        assert move(client, auth["clin"], r["case_id"], ending).status_code == 409


def test_navigator_cannot_confirm_arrival_only_the_facility_side_can(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    for state in TO_ARRIVAL[:-1]:
        assert move(client, auth["nav"], cid, state).status_code == 200
    assert move(client, auth["nav"], cid, "ARRIVAL_CONFIRMED").status_code == 403
    assert move(client, auth["clin"], cid, "ARRIVAL_CONFIRMED").status_code == 200


def test_missed_appointment_can_return_to_navigation_and_rebook(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    walk(client, auth, cid, TO_ARRIVAL[:-1])  # up to APPOINTMENT_BOOKED
    assert (
        move(
            client, auth["nav"], cid, "NAVIGATION_ACTIVE", "Missed visit; helping to rebook"
        ).status_code
        == 200
    )
    assert move(client, auth["nav"], cid, "APPOINTMENT_BOOKED").status_code == 200


def test_cannot_close_without_evidence(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    walk(client, auth, cid, TO_HANDOFF)
    resp = client.post(f"/api/v1/cases/{cid}/close", json={}, headers=auth["clin"])
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "evidence_required"


def test_cannot_close_before_handoff_even_with_evidence(client, auth, make_case):
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
    walk(client, auth, cid, TO_HANDOFF)
    resp = client.post(
        f"/api/v1/cases/{cid}/close",
        json={
            "evidence_type": "facility_confirmation",
            "description": "Synthetic: facility reports care initiated",
        },
        headers=auth["nav"],
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "CLOSED"
    assert body["closure_reason"] == "facility_confirmation"
    assert body["deadline_at"] is None
    assert (
        move(client, auth["clin"], cid, "PATIENT_ENGAGED").status_code == 409
    )  # closed cases stay closed


def test_close_with_previously_attached_evidence(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    walk(client, auth, cid, TO_HANDOFF)
    ev = client.post(
        f"/api/v1/cases/{cid}/evidence",
        json={"type": "follow_up_plan_documented", "description": "Synthetic"},
        headers=auth["nav"],
    )
    assert ev.status_code == 201
    assert (
        client.post(f"/api/v1/cases/{cid}/close", json={}, headers=auth["clin"]).status_code == 200
    )


def test_bad_evidence_type_is_rejected(client, auth, make_case):
    _, r = make_case()
    resp = client.post(
        f"/api/v1/cases/{r['case_id']}/evidence",
        json={"type": "vibes", "description": "x"},
        headers=auth["clin"],
    )
    assert resp.status_code == 422


def test_patient_can_decline_and_it_is_recorded(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    move(client, auth["nav"], cid, "PATIENT_ENGAGED")
    assert (
        client.post(
            f"/api/v1/cases/{cid}/decline", json={"note": ""}, headers=auth["nav"]
        ).status_code
        == 422
    )  # note required
    resp = client.post(
        f"/api/v1/cases/{cid}/decline",
        json={"note": "Patient said she does not want to continue"},
        headers=auth["nav"],
    )
    assert resp.status_code == 200
    assert resp.json()["state"] == "PATIENT_DECLINED"
    assert resp.json()["closure_reason"] == "patient_declined"
    assert client.get("/api/v1/cases", headers=auth["nav"]).json() == []
    assert move(client, auth["nav"], cid, "BARRIERS_ASSESSED").status_code == 409


def test_decline_is_not_available_after_handoff(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    walk(client, auth, cid, TO_HANDOFF)
    resp = client.post(f"/api/v1/cases/{cid}/decline", json={"note": "x"}, headers=auth["nav"])
    assert resp.status_code == 409


def test_timeline_records_every_move_in_order(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    move(client, auth["nav"], cid, "PATIENT_ENGAGED", "patient joined")
    events = client.get(f"/api/v1/cases/{cid}/timeline", headers=auth["nav"]).json()
    assert [e["to_state"] for e in events] == ["SCREENING_FLAGGED", "PATIENT_ENGAGED"]
    assert events[1]["note"] == "patient joined"
    assert events[1]["actor_name"] == "Nav"


def test_claim_makes_case_owned(client, auth, make_case):
    _, r = make_case()
    resp = client.post(f"/api/v1/cases/{r['case_id']}/claim", headers=auth["nav"])
    assert resp.json()["unowned"] is False
    assert resp.json()["owner_user_name"] == "Nav"
    assert client.get("/api/v1/cases?unowned=true", headers=auth["nav"]).json() == []


def test_state_changes_and_refusals_are_audited(client, auth, make_case):
    _, r = make_case()
    cid = r["case_id"]
    move(client, auth["nav"], cid, "PATIENT_ENGAGED")
    move(client, auth["clin"], cid, "HANDED_OFF")  # invalid, refused
    entries = client.get(
        "/api/v1/audit?entity_type=care_case&limit=100", headers=auth["admin"]
    ).json()
    actions = [(e["action"], e["outcome"]) for e in entries]
    assert ("case.open", "success") in actions
    assert ("case.transition", "success") in actions
    assert ("case.transition", "rejected") in actions


def test_close_with_evidence_type_but_no_description_is_a_clean_validation_error(
    client, auth, make_case
):
    _, r = make_case()
    resp = client.post(
        f"/api/v1/cases/{r['case_id']}/close",
        json={"evidence_type": "clinician_decision"},
        headers=auth["clin"],
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"
