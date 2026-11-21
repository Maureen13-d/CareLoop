"""The optional model may reword one approved line and may not add a claim."""

from app.modules.followup import telegram_phrase as phrase


def _use(monkeypatch, completer):
    monkeypatch.setenv("CARELOOP_LLM_API_KEY", "test-key")
    phrase.set_complete(completer)


def teardown_function():
    phrase.set_complete(None)


def test_no_key_leaves_the_approved_line(monkeypatch):
    monkeypatch.setenv("CARELOOP_LLM_API_KEY", "")
    messages = [{"template_id": "visit_bring", "text": "Bring your card."}]
    assert phrase.phrase_messages(messages, "en")[0]["text"] == "Bring your card."


def test_worse_is_never_sent_to_the_model(monkeypatch):
    calls = []

    def completer(system, user):
        calls.append(user)
        return "You are fine."

    _use(monkeypatch, completer)
    messages = [{"template_id": "worse", "text": "Please go to the nearest clinic now.", "urgent": True}]
    out = phrase.phrase_messages(messages, "en")
    assert out[0]["text"] == "Please go to the nearest clinic now."
    assert calls == []


def test_reassurance_is_thrown_away(monkeypatch):
    _use(monkeypatch, lambda system, user: "You are fine. Nothing to worry about.")
    messages = [{"template_id": "same", "text": "Please still go to your clinic."}]
    out = phrase.phrase_messages(messages, "en")
    assert out[0]["text"] == "Please still go to your clinic."
    assert "phrased" not in out[0]


def test_rewording_keeps_the_clinic_and_the_review_line(monkeypatch):
    approved = "Clinic: Demo Clinic, 8 to 4.\nSource: CareLoop draft. PENDING CLINICAL REVIEW."

    def completer(system, user):
        return "Go to Demo Clinic between 8 and 4. PENDING CLINICAL REVIEW."

    _use(monkeypatch, completer)
    messages = [{"template_id": "visit_time", "text": approved}]
    out = phrase.phrase_messages(messages, "en")
    assert out[0]["text"].startswith("Go to Demo Clinic")
    assert out[0]["phrased"] is True


def test_dropping_the_clinic_name_is_rejected(monkeypatch):
    _use(monkeypatch, lambda system, user: "Please go to the clinic at 8.")
    approved = "Clinic: Demo Clinic, 8 to 4."
    messages = [{"template_id": "next_step", "text": approved}]
    assert phrase.phrase_messages(messages, "en")[0]["text"] == approved


def test_route_only_accepts_an_offered_key(monkeypatch):
    _use(monkeypatch, lambda system, user: "worse")
    assert phrase.route("I feel awful", {"visit_bring": "Bring your card."}) is None


def test_route_returns_a_known_key(monkeypatch):
    _use(monkeypatch, lambda system, user: "visit_bring")
    picked = phrase.route("what should I take with me?", {"visit_bring": "Bring your card."})
    assert picked == "visit_bring"


def test_route_without_a_key_does_not_guess(monkeypatch):
    monkeypatch.setenv("CARELOOP_LLM_API_KEY", "")
    assert phrase.route("what should I take?", {"visit_bring": "Bring your card."}) is None


def test_a_reword_keeps_the_named_person_and_clinic(monkeypatch):
    approved = (
        "If you have any issue with it, ask Grace. "
        "You can go to Hill clinic, Tue and Thu, 8 to 12, and ask."
    )

    def completer(system, user):
        return "Ask Grace at Hill clinic between 8 and 12."

    _use(monkeypatch, completer)
    messages = [
        {
            "template_id": "refuse_diagnosis_both",
            "text": approved,
            "facts": ["Grace", "Hill clinic"],
        }
    ]
    out = phrase.phrase_messages(messages, "en")
    assert out[0]["phrased"] is True
    assert "Grace" in out[0]["text"]
    assert "Hill clinic" in out[0]["text"]


def test_dropping_the_person_is_rejected(monkeypatch):
    approved = "If you have any issue with it, ask Grace."
    _use(monkeypatch, lambda system, user: "If you have any issue with it, ask at the clinic.")
    messages = [{"template_id": "refuse_diagnosis_person", "text": approved, "facts": ["Grace"]}]
    assert phrase.phrase_messages(messages, "en")[0]["text"] == approved


def test_a_new_hospital_name_is_rejected(monkeypatch):
    approved = "If you have any issue with it, ask Grace."
    _use(monkeypatch, lambda system, user: "If you have any issue with it, ask Grace at Kenyatta.")
    messages = [{"template_id": "refuse_diagnosis_person", "text": approved, "facts": ["Grace"]}]
    assert phrase.phrase_messages(messages, "en")[0]["text"] == approved
