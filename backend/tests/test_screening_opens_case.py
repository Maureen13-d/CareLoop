def test_positive_screening_opens_case_with_owner_and_deadline(client, auth, make_case):
    _, result = make_case("positive")
    assert result["case_status"] == "opened"
    case = client.get(f"/api/v1/cases/{result['case_id']}", headers=auth["nav"]).json()
    assert case["state"] == "SCREENING_FLAGGED"
    assert case["owner_department"] == "Screening clinic"
    assert case["deadline_at"].endswith("Z")
    assert case["unowned"] is True
    assert case["overdue"] is False


def test_negative_screening_opens_no_case(make_case):
    _, result = make_case("negative")
    assert result["case_status"] == "not_required"
    assert result["case_id"] is None


def test_suspected_cancer_is_urgent(client, auth, make_case):
    _, result = make_case("suspected_cancer")
    case = client.get(f"/api/v1/cases/{result['case_id']}", headers=auth["clin"]).json()
    assert case["urgency"] == "urgent"


def test_no_consent_blocks_case_but_saves_screening(make_case):
    _, result = make_case("positive", consent=False)
    assert result["case_status"] == "no_consent"
    assert result["case_id"] is None
    assert result["screening"]["result"] == "positive"


def test_second_positive_does_not_duplicate_open_case(client, auth, make_case):
    patient, first = make_case("positive")
    again = client.post(f"/api/v1/patients/{patient['id']}/screenings",
                        json={"screening_type": "VIA", "result": "positive"}, headers=auth["clin"]).json()
    assert again["case_status"] == "already_open"
    assert again["case_id"] == first["case_id"]


def test_navigator_cannot_record_screening(client, auth, make_case):
    patient, _ = make_case("negative")
    resp = client.post(f"/api/v1/patients/{patient['id']}/screenings",
                       json={"screening_type": "VIA", "result": "positive"}, headers=auth["nav"])
    assert resp.status_code == 403


def test_withdrawn_consent_blocks_new_case(client, auth, make_case):
    patient, _ = make_case("negative")
    client.post(f"/api/v1/patients/{patient['id']}/consents", json={"purpose": "care_coordination", "granted": False}, headers=auth["nav"])
    resp = client.post(f"/api/v1/patients/{patient['id']}/screenings",
                       json={"screening_type": "HPV_DNA", "result": "positive"}, headers=auth["clin"]).json()
    assert resp["case_status"] == "no_consent"
