def test_assistant_endpoint_needs_login(client):
    assert client.post("/api/v1/assistant/message", json={"text": "hello"}).status_code == 401


def test_assistant_endpoint_replies_and_audits_labels_only(client, auth):
    resp = client.post("/api/v1/assistant/message",
                       json={"channel": "sms", "text": "how much will it cost, my husband beats me"}, headers=auth["nav"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["tier"] == "lite" and body["barrier_flags"][0]["flag"] == "cost"

    entries = client.get("/api/v1/audit?action=assistant.message", headers=auth["admin"]).json()
    assert len(entries) == 1
    detail = entries[0]["detail"]
    assert detail["tier"] == "lite" and "cost" in detail["flags"]
    assert "husband" not in str(entries[0]).lower()      # the patient's words are never audited


def test_assistant_rejects_an_empty_request(client, auth):
    assert client.post("/api/v1/assistant/message", json={"channel": "sms"}, headers=auth["nav"]).status_code == 422
