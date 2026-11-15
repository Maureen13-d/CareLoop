import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import clock
from app.core.db import Base, get_db, import_models, make_engine
from app.core.security import hash_password
from app.main import app
from app.modules.auth.models import Department, User

PASSWORD = "test-password"
PASSWORD_HASH = hash_password(PASSWORD)  # hashed once; scrypt is deliberately slow
DEPARTMENTS = [
    ("screening_clinic", "Screening clinic"),
    ("care_coordination", "Care coordination"),
    ("gynaecology_clinic", "Gynaecology clinic"),
    ("treatment_unit", "Treatment unit"),
]
USERS = [
    ("coord", "coordinator", "care_coordination"),
    ("clin", "clinician", "gynaecology_clinic"),
    ("manager", "program_manager", None),
    ("admin", "admin", None),
]


@pytest.fixture()
def db_session():
    engine = make_engine("sqlite://", poolclass=StaticPool)
    import_models()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    depts = {}
    for name, label in DEPARTMENTS:
        d = Department(name=name, label=label)
        session.add(d)
        depts[name] = d
    session.flush()
    for username, role, dept in USERS:
        session.add(User(username=username, password_hash=PASSWORD_HASH, role=role,
                         display_name=username.title(), department_id=depts[dept].id if dept else None))
    session.commit()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def client(db_session):
    clock.reset()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)  # no "with": the real lifespan (and real database) is never started
    app.dependency_overrides.clear()
    clock.reset()


def login(client, username):
    resp = client.post("/api/v1/auth/login", data={"username": username, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def auth(client):
    return {name: login(client, name) for name, _, _ in USERS}


@pytest.fixture()
def make_case(client, auth):
    """Create a consenting patient and a positive screening; returns the case id."""

    def _make(result="positive", consent=True):
        patient = client.post("/api/v1/patients", json={"display_name": "Demo Patient", "age_band": "30-34"},
                              headers=auth["coord"]).json()
        if consent:
            r = client.post(f"/api/v1/patients/{patient['id']}/consents",
                            json={"purpose": "care_coordination", "granted": True}, headers=auth["coord"])
            assert r.status_code == 201, r.text
        resp = client.post(f"/api/v1/patients/{patient['id']}/screenings",
                           json={"screening_type": "HPV_DNA", "result": result}, headers=auth["clin"])
        assert resp.status_code == 201, resp.text
        return patient, resp.json()

    return _make
