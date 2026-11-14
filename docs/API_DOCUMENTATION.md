# API Documentation

Status: **design contract**. Endpoints are proposals; update this file in the same PR that changes an endpoint. The backend will also publish interactive docs at `/docs` (FastAPI) once it exists.

## Conventions

- Base path: `/api/v1`. JSON in and out. `snake_case` field names.
- Authentication: bearer token (JWT) from `POST /auth/login`. Every endpoint except `/health` and `/auth/login` needs a token.
- Authorisation: role checked on every endpoint (see [SECURITY_AND_PRIVACY.md](SECURITY_AND_PRIVACY.md)).
- Timestamps: ISO 8601 in UTC.
- Pagination: `limit` (default 25, max 100) and `offset`.
- Errors use one shape:

```json
{ "error": { "code": "invalid_transition", "message": "Case cannot move from OPENED to TREATMENT_STARTED", "details": {} } }
```

- Status codes: 200 OK, 201 Created, 400 bad request, 401 not authenticated, 403 not allowed for this role, 404 not found, 409 conflict (for example invalid state change), 422 validation error.
- Every state-changing call writes an audit event.

## MVP endpoints

| Group | Method and path | Purpose | Roles |
|---|---|---|---|
| System | `GET /health` | Liveness check | public |
| Auth | `POST /auth/login` | Get a token | public |
| Auth | `GET /auth/me` | Current user and role | any |
| Patients | `GET /patients`, `GET /patients/{id}`, `POST /patients` | Synthetic patient records | coordinator, clinician |
| Consents | `POST /patients/{id}/consents` | Record or revoke a consent | coordinator, clinician |
| Screenings | `POST /patients/{id}/screenings` | Record a result; positive results open a case | clinician |
| Cases | `GET /cases` | List with filters `state`, `overdue`, `owner`, `urgency` | coordinator, clinician, program_manager (limited) |
| Cases | `GET /cases/{id}` | Case detail | coordinator, clinician |
| Cases | `GET /cases/{id}/timeline` | Ordered events | coordinator, clinician |
| Cases | `POST /cases/{id}/transitions` | Body `{to_state, note}`; invalid moves return 409 | coordinator, clinician |
| Cases | `POST /cases/{id}/evidence` | Attach evidence | clinician, coordinator |
| Cases | `POST /cases/{id}/close` | Needs evidence or a recorded decision | clinician |
| Referrals | `POST /cases/{id}/referrals` | Create a referral | coordinator, clinician |
| Referrals | `POST /referrals/{id}/accept`, `/reject`, `/complete` | Update status; reject needs a reason | clinician |
| Tasks | `GET /tasks`, `POST /cases/{id}/tasks`, `PATCH /tasks/{id}` | Task tracking | coordinator, clinician |
| Appointments | `POST /cases/{id}/appointments`, `PATCH /appointments/{id}` | Schedule, mark attended or missed | coordinator, clinician |
| Notifications | `POST /cases/{id}/notifications/draft` | Create a draft from an approved template | coordinator |
| Notifications | `GET /notifications?status=drafted` | Review queue | coordinator |
| Notifications | `POST /notifications/{id}/approve`, `/reject` | Human review; approve sends to the simulated outbox | coordinator |
| Notifications | `POST /notifications/{id}/acknowledge` | Simulated patient acknowledgement | public demo link (token) |
| Escalations | `GET /escalations`, `POST /escalations/{id}/resolve` | Handle escalations | coordinator, clinician |
| Analytics | `GET /analytics/summary`, `GET /analytics/pathway-metrics` | Aggregate metrics | program_manager, coordinator |
| Audit | `GET /audit` | Filtered audit log | admin, program_manager |
| Admin (demo) | `POST /admin/run-deadline-check`, `POST /admin/reset-demo` | Demo controls | admin |

## Stretch endpoints

- `GET /cases/{id}/risk` (risk score with contributing factors)
- `POST /assistant/draft-summary`, `POST /assistant/draft-message` (draft only; output goes to the review queue)
- `GET /fhir/Patient/{id}` and similar (simulated export)

## Example: transition request

```http
POST /api/v1/cases/42/transitions
Authorization: Bearer <token>
Content-Type: application/json

{ "to_state": "PATIENT_NOTIFIED", "note": "Message approved and sent (simulated)" }
```

Success returns the updated case, the new owner and the new deadline. An invalid move returns 409 `invalid_transition`.
