# Audit: KSL signing avatar

Date: 21 Nov 2026. Base: `feat/screening-to-care-loop` at `3686129`.
This audit does not change behaviour. No avatar, no clip registry, and no recogniser are built here.

CareLoop follows a person from a concerning screening to a confirmed clinic visit. A Deaf Kenyan Sign Language (KSL) user is excluded by speech, and by a flow that depends on written English or Kiswahili. The avatar, when it is built, plays approved recorded signing. It does not translate free text and it does not invent signs.

## Stack

| Layer | What is in the repo now |
|---|---|
| Web | Next.js 16, React 19, TypeScript, Tailwind. No Three.js, no React Three Fiber, no glTF loader. |
| API | Python, FastAPI, SQLAlchemy. Tables are created with `Base.metadata.create_all` in `backend/app/core/db.py`. There is no Alembic migration tree. |
| Lines | Fixed text in `ai/templates/followup.yaml`, marked pending clinical review. Keys are loaded by `backend/app/modules/followup/texts.py`. |
| Patient card | `frontend/src/app/enter/EnterFlow.tsx`. A circle pulses, captions show `reply_text`, and the browser speaks that same text. |
| Channels | Web, a Telegram simulator, and a USSD contract. SMS length is cut to 160 ASCII characters. USSD is cut to 182 characters. |

Player choice for the later build, not installed in this commit: React Three Fiber on Three.js. The card is already a React client component, and the avatar has to sit in that page, load one glTF rig, and play a motion packet. A separate canvas page would split the patient flow.

## Language handling

`Language` in `backend/app/modules/followup/schemas.py` is `en` or `sw` only. The same limit is on the enrolment and on the channel session (`backend/app/modules/followup/models.py`).

Opening a session asks "1 English / 2 Kiswahili" (`handle` in `conversation.py`). There is no `ksl` value. Kiswahili lines exist and are drafts.

Roles in `backend/app/modules/auth/models.py` are navigator, clinician, counsellor, patient, program manager, admin, and CHW. There is no `ksl_reviewer` role.

## What the conversation core returns

`respond` and `handle` in `backend/app/modules/followup/conversation.py` return a dict from `_pack`:

| Field | Meaning |
|---|---|
| `reply_text` | The fixed line for the reply key, trimmed for SMS or USSD. |
| `quick_replies` | A short menu, or English / Kiswahili at the language step. |
| `actions` | Labels such as `open_task`, `stop`, `barrier_confirmed`. |
| `escalation_label` | `danger_sign`, `distress`, `worse`, `unclear`, or empty. |

The reply key (`status`, `worse`, `danger`, and the rest) is used to pick the line and is not returned. There is no `template_id` and no `ksl` object. A later change has to add those fields without changing the safety order: danger and distress first, then a fixed menu, then one task for unclear or worse. The core must still never say the person is fine.

`guide_speaks` returns the reply text and nothing else. The card speaks that string. A KSL clip has to be tied to the same reply key, and the caption has to stay equal to the current line.

## Where the avatar fits

```text
conversation.respond
    reply key + reply_text + escalation_label
            |
            v
clip registry (not built)  -- approved and hash matches? -- no --> fallback ladder
            |
            v yes
motion packet + caption + rendered video URL
            |
            v
patient card /enter          Telegram: rendered video only
USSD and SMS stay text. They cannot show an avatar.
```

The pulsing circle in `EnterFlow.tsx` is not a signer. Danger already skips the pulse and shows the line in large type. That screen must stay immediate. Animation must not cover "go to the nearest clinic now".

CHW actions today are call, home visit, transport support, counsellor, and escalate to clinician (`config/followup_worklist.yaml`). A phone call is the first action. For a Deaf user that list is the wrong default. It is unchanged in this audit.

## Feature gap

| ID | Title | Status | What already exists | What is missing |
|---|---|---|---|---|
| K00 | Audit and plan | Done in this document | Stack, languages, core return shape, and the card. | Nothing further for this feature. |
| K01 | Asset policy | Not started | `.gitignore` blocks model weights and local databases. CI runs ruff, a subset of pytest, and the frontend build. | Ignore rules and a CI check for raw video, raw mocap, signer photos, and oversized binaries. |
| K02 | Motion packet spec | Not started | No motion format. | `docs/KMP_SPEC.md`, a JSON schema, a validator, and a test clip labelled `TEST_MOTION_NOT_SIGN`. |
| K03 | Clip tables and manifest | Not started | `create_all` on SQLAlchemy models. Lines live in YAML. | `ksl_signers`, `ksl_clips`, `ksl_reviews`, and `config/ksl_phrase_manifest.yaml`. No signer names or photos in the database. |
| K04 | Clip registry API | Not started | Follow-up routes under the API. | `GET /ksl/clip/{template_id}` serves a clip only when it is approved and the source-text hash still matches. |
| K05 | Review workflow | Not started | Staff roles, no reviewer role. | Deaf review, back-translation, and a second person to approve. The approver cannot be the uploader. |
| K06 | Avatar rig | Not started | No glTF, no Three.js. | One upper-body rig with fingers, 52 face shapes, gaze, and at least four appearance presets. |
| K07 | Playback | Not started | No player. | Blend in and out, co-articulation, speed, pause, replay, step-through, time-based frame pacing. |
| K08 | Non-manual channels | Not started | No face or gaze channels. | Recorded face, gaze, head, and torso win over any idle motion while a clip plays. |
| K09 | Idle and attention | Not started | A CSS pulse, and `motion-reduce:animate-none` on that pulse. | Idle only between clips. Reduce motion uses step-through and captions, not a frozen sign. |
| K10 | Appearance presets | Not started | No avatar mesh. | Skin, hair, and plain contrasting clothes. The user can switch. |
| K11 | Fallback ladder | Not started | The card always shows text. Speech can be muted. | One module: avatar, then rendered video, then captions with icons, then a human task. |
| K12 | Core integration | Not started | Core returns text only. Languages are `en` and `sw`. | Add `ksl` and `{template_id, ksl:{available, clip_id, fallback}}`. Caption equals the template line. |
| K13 | Telegram video | Not started | Telegram simulator posts text through the same core. | Send the rendered approved clip, or captions plus a human task. |
| K14 | Deaf-aware follow-up | Not started | Worklist ranks worse first. Actions start with call. | Sooner escalation, no phone call as the main action, an interpreter-needed barrier on the facility view. |
| K15 | Guided call | Not started | Quick replies are taps on fixed labels. | A state machine and a simulator recogniser. No trained model. Taps stay the primary input. |
| K16 | Docs | Not started | `docs/LIMITATIONS.md` covers the screening prototype. | Design, packet spec, data plan, consent outline, validation protocol, demo script. Limits updated. |
| K17 | Tag `ksl-ready` | Not started | No such tag. | Only after the checks in the feature list pass. |

## Rules that already match, and must stay

- The core does not generate text. Patient wording is not stored in the audit log. The audit stores a label, the channel, and the escalation.
- Worse, danger, distress, a diagnosis request, and unclear input open a task. `same` and `better` still tell the person to go to the clinic.
- Outbound lines do not name a condition or a screening type.
- Demo data is synthetic. Tests use an in-memory database and do not write `backend/careloop.db`.

## Decisions left open

- Clip packs, once a Deaf signer has signed a consent, go to Git LFS or to storage outside the repo. Raw footage does not go to either as a git object.
- New tables should follow `create_all` unless the team chooses to introduce Alembic. This audit does not choose Alembic.
- No real KSL clip exists. Until Deaf reviewers approve recorded motion, any stand-in must be labelled `PLACEHOLDER MOTION: NOT KSL` and must be refused in production.

## What this audit does not claim

Signvrse's Terp 360 is a reference for recorded mocap driving a 3D avatar. CareLoop has no partnership, no capture, and no permission to use anyone's motion data. Dataset sizes cited in the task brief are not verified here. They will be checked in the data plan before any file is downloaded.
