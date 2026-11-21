"""Clips are served only after approval, and only while the template line still matches."""

from sqlalchemy import select

from app.modules.auth.models import User
from app.modules.ksl.kmp import TEST_LABEL, source_hash
from app.modules.ksl.manifest import current_caption
from app.modules.ksl.models import KslClip
from app.modules.ksl.registry import serve

PASSWORD = "test-password"


def _login(client, username):
    resp = client.post("/api/v1/auth/login", data={"username": username, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _reviewer(db_session, username):
    admin = db_session.scalar(select(User).where(User.username == "admin"))
    db_session.add(
        User(
            username=username,
            password_hash=admin.password_hash,
            role="ksl_reviewer",
            display_name=username,
        )
    )
    db_session.commit()
    return username


def _prepare(client, headers):
    signer = client.post("/api/v1/ksl/signers", json={"pseudonym": "signer-a"}, headers=headers["admin"])
    assert signer.status_code == 201, signer.text
    clip = client.post(
        "/api/v1/ksl/clips",
        json={
            "template_id": "status",
            "signer_id": signer.json()["id"],
            "label": "recorded",
            "motion_uri": "assets/ksl/approved/status.kmp",
            "video_uri": "assets/ksl/approved/status.mp4",
        },
        headers=headers["admin"],
    )
    assert clip.status_code == 201, clip.text
    return signer.json()["id"], clip.json()["id"]


def _pass(client, headers, clip_id):
    first = client.post(
        f"/api/v1/ksl/clips/{clip_id}/reviews",
        json={"kind": "deaf_review", "result": "pass"},
        headers=headers["deaf1"],
    )
    assert first.status_code == 201, first.text
    second = client.post(
        f"/api/v1/ksl/clips/{clip_id}/reviews",
        json={"kind": "back_translation", "result": "pass"},
        headers=headers["deaf2"],
    )
    assert second.status_code == 201, second.text


def test_unapproved_stale_and_revoked_clips_are_not_served(client, db_session):
    _reviewer(db_session, "deaf1")
    _reviewer(db_session, "deaf2")
    headers = {
        "admin": _login(client, "admin"),
        "manager": _login(client, "manager"),
        "deaf1": _login(client, "deaf1"),
        "deaf2": _login(client, "deaf2"),
    }
    signer_id, clip_id = _prepare(client, headers)
    hidden = client.get("/api/v1/ksl/clip/status")
    assert hidden.status_code == 200
    assert hidden.json()["available"] is False

    blocked = client.post(f"/api/v1/ksl/clips/{clip_id}/approve", headers=headers["manager"])
    assert blocked.status_code == 409

    first = client.post(
        f"/api/v1/ksl/clips/{clip_id}/reviews",
        json={"kind": "deaf_review", "result": "pass"},
        headers=headers["deaf1"],
    )
    assert first.status_code == 201, first.text
    same = client.post(
        f"/api/v1/ksl/clips/{clip_id}/reviews",
        json={"kind": "back_translation", "result": "pass"},
        headers=headers["deaf1"],
    )
    assert same.status_code == 409

    second = client.post(
        f"/api/v1/ksl/clips/{clip_id}/reviews",
        json={"kind": "back_translation", "result": "pass"},
        headers=headers["deaf2"],
    )
    assert second.status_code == 201, second.text
    own = client.post(f"/api/v1/ksl/clips/{clip_id}/approve", headers=headers["admin"])
    assert own.status_code == 403
    approved = client.post(f"/api/v1/ksl/clips/{clip_id}/approve", headers=headers["manager"])
    assert approved.status_code == 200, approved.text
    body = approved.json()
    assert body["status"] == "approved"
    assert body["pilot_enabled"] is False

    served = client.get("/api/v1/ksl/clip/status").json()
    assert served["available"] is True
    assert served["caption"] == current_caption("status")
    assert served["clip_id"] == clip_id
    assert "you are fine" not in served["caption"].lower()

    row = db_session.get(KslClip, clip_id)
    row.source_text_hash = "0" * 64
    db_session.commit()
    stale = client.get("/api/v1/ksl/clip/status").json()
    assert stale["available"] is False
    assert db_session.get(KslClip, clip_id).status == "stale"

    row = db_session.get(KslClip, clip_id)
    row.status = "approved"
    row.source_text_hash = source_hash(current_caption("status"))
    db_session.commit()
    revoked = client.post(f"/api/v1/ksl/signers/{signer_id}/revoke", headers=headers["admin"])
    assert revoked.json()["retired"] == 1
    gone = client.get("/api/v1/ksl/clip/status").json()
    assert gone["available"] is False
    assert db_session.get(KslClip, clip_id).status == "retired"


def test_production_refuses_placeholder_labels(client, db_session):
    _reviewer(db_session, "deaf1")
    _reviewer(db_session, "deaf2")
    headers = {
        "admin": _login(client, "admin"),
        "manager": _login(client, "manager"),
        "deaf1": _login(client, "deaf1"),
        "deaf2": _login(client, "deaf2"),
    }
    signer = client.post("/api/v1/ksl/signers", json={"pseudonym": "synthetic"}, headers=headers["admin"])
    clip = client.post(
        "/api/v1/ksl/clips",
        json={
            "template_id": "hello",
            "signer_id": signer.json()["id"],
            "label": TEST_LABEL,
            "motion_uri": "assets/ksl/placeholders/test_motion.json",
        },
        headers=headers["admin"],
    )
    _pass(client, headers, clip.json()["id"])
    client.post(f"/api/v1/ksl/clips/{clip.json()['id']}/approve", headers=headers["manager"])
    assert serve(db_session, "hello", production=True)["available"] is False
    assert serve(db_session, "hello", production=False)["label"] == TEST_LABEL
