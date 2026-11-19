# API Documentation

Status: **design contract**. Endpoints are proposals; update this file in the same PR that changes an endpoint. The backend will also publish interactive docs at `/docs` (FastAPI) once it exists.

## Conventions

- Base path: `/api/v1`. JSON in and out. `snake_case` field names.
- Authentication: bearer token (JWT) from `POST /auth/login`. Every endpoint except `/health`, `/auth/login` and the simulated channel endpoints needs a token.
- Authorisation: role checked on every endpoint (see [SECURITY_AND_PRIVACY.md](SECURITY_AND_PRIVACY.md)).
- Timestamps: ISO 8601 in UTC.
- Pagination: `limit` (default 25, max 100) and `offset`.
- Errors use one shape:

```json
{ "error": { "code": "invalid_transition", "message": "Case cannot move from FLAGGED to HANDED_OFF", "details": {} } }
```

- Status codes: 200 OK, 201 Created, 400 bad request, 401 not authenticated, 403 not allowed for this role, 404 not found, 409 conflict (for example invalid state change), 422 validation error.
- Every state-changing call writes an audit event.

## MVP endpoints

| Group | Method and path | Purpose | Roles |
|---|---|---|---|
| System | `GET /health` | Liveness check | public |
| Auth | `POST /auth/login` | Get a token | public |
| Auth | `GET /auth/me` | Current user and role | any |
| Patients | `GET /patients`, `GET /patients/{id}`, `POST /patients` | Synthetic patient records | navigator, clinician |
| Consents | `POST /patients/{id}/consents` | Record or revoke a consent | navigator, clinician |
| Screenings | `POST /patients/{id}/screenings` | Screener records a concerning finding (not a diagnosis); with consent this opens a case | clinician, navigator |
| Cases | `GET /cases` | List with filters `state`, `overdue`, `owner`, `urgency` | navigator, clinician, program_manager (limited) |
| Cases | `GET /cases/{id}` | Case detail | navigator, clinician |
| Cases | `GET /cases/{id}/timeline` | Ordered events | navigator, clinician |
| Cases | `POST /cases/{id}/transitions` | Body `{to_state, note}`; invalid moves return 409 | navigator, clinician |
| Cases | `POST /cases/{id}/evidence` | Attach evidence; hospital milestones from the mock hospital are stored as evidence | clinician, navigator |
| Cases | `POST /cases/{id}/close` | Needs a hospital milestone or a recorded human decision with a reason | clinician, navigator |
| Cases | `POST /cases/{id}/claim` | Take ownership of a case | navigator, clinician |
| Cases | `POST /cases/{id}/mark-lost` | Record a human decision that the person is lost to follow-up, after navigator attempts | navigator, clinician |
| Barriers | `GET /cases/{id}/barriers`, `POST /barriers/{id}/confirm` | List detected barriers; the person's confirmation lets a navigator see them | navigator, patient (via channel) |
| Assistant | `POST /assistant/message` | Web chat: safety rules, then Lite mode, then retrieval. Crisis text returns a human handoff | patient |
| Tasks | `GET /navigator/tasks`, `PATCH /navigator/tasks/{id}` | Navigator worklist; tasks are created by the system or by a navigator | navigator |
| Appointments | `POST /cases/{id}/appointments/request`, `PATCH /appointments/{id}` | Request a visit, confirm, mark attended or missed; a missed visit creates a navigator task | navigator |
| Channels | `POST /channels/ussd` | Simulated USSD callback: session, phone reference and text in, menu screen out | public (simulator) |
| Channels | `POST /channels/sms/inbound` | Simulated inbound SMS: reply codes 1, 2, 3 and STOP | public (simulator) |
| Channels | `GET /sim/sms-outbox` | Simulated SMS outbox shown in the simulator; an undelivered message creates a navigator task | public (simulator) |
| Interop | `POST /interop/appointment-request`, `POST /interop/milestones` | Send a FHIR Appointment request to the mock hospital; receive milestones back (stored as case evidence). Invalid FHIR returns 422 | system |
| Analytics | `GET /analytics/summary`, `GET /analytics/funnel` | Aggregate metrics and the pathway funnel | program_manager, navigator |
| Audit | `GET /audit` | Filtered audit log | admin, program_manager |
| Admin (demo) | `POST /admin/run-deadline-check`, `POST /admin/reset-demo` | Demo controls | admin |

## Stretch endpoints

- Optional language-model mode for `POST /assistant/message` (web chat only; Lite mode stays the fallback)
- Kiswahili lexicon and templates for Lite mode (needs a fluent reviewer)
- Provider sandbox adapter for SMS or USSD (the simulator stays the default)

## Example: transition request

```http
POST /api/v1/cases/42/transitions
Authorization: Bearer <token>
Content-Type: application/json

{ "to_state": "ENGAGED", "note": "Person joined through the simulated USSD menu" }
```

Success returns the updated case, the new owner and the new deadline. An invalid move returns 409 `invalid_transition`.
