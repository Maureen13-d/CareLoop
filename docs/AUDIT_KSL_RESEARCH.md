# KSL research-mode audit

Baseline: `feat/ksl-avatar` at `aa89055`. This audit describes that tree before any research-mode code. No Kenyan Sign Language dataset is in the repository. No research clip exists. Nothing here is a reviewed patient message.

## Avatar

| Piece | Where | What it does |
|---|---|---|
| Playback clock | `frontend/src/ksl/engine.js` | Plays a recorded motion packet. It does not invent signs. Placeholder clips carry `PLACEHOLDER MOTION: NOT KSL`. |
| On-screen guide | `frontend/src/ksl/SigningAvatar.tsx` | Draws a simple figure from the player. Danger replies stay as text. An unavailable clip shows the placeholder, the caption, and icons. |
| Patient card | `frontend/src/app/enter/EnterFlow.tsx` | The only patient page that mounts the avatar. |
| Staff clip list | `frontend/src/app/(app)/ksl/page.tsx` | Lists clip labels for review. It does not play motion. |
| Rig | `assets/ksl/rig/guide.gltf` | Joint names for later playback. The rig is not a recorded signer. |

## Motion packet

`backend/app/modules/ksl/kmp.py` defines the packet: body joints, hand joints, face shapes, head pose, 30 fps, and a source-text hash. `docs/KMP_SPEC.md` and `schemas/kmp-1.schema.json` match that packet. `assets/ksl/placeholders/test_motion.json` is synthetic. Its label is `TEST_MOTION_NOT_SIGN`.

`blocked_in_production` refuses only `TEST_MOTION_NOT_SIGN` and `PLACEHOLDER MOTION: NOT KSL` when production mode is on. Approved clips with any other label can still be served.

## Clip registry

`backend/app/modules/ksl/registry.py` `serve` returns a clip only when all of these hold:

- The template id has a current caption in `config/ksl_phrase_manifest.yaml` or the English follow-up templates.
- A `KslClip` row for that template is `approved`.
- `source_text_hash` still matches the caption.
- The signer has not revoked consent.
- Production mode is off, or the clip label is not a test or placeholder label.

`for_channel` sends motion on the web, a rendered `video_url` on Telegram, and text only on SMS and USSD. There is no path that loads an external pose file.

Review rules live in `backend/app/modules/ksl/review.py`. Two Deaf passes and a different confirmer are required before approval. The fallback ladder in `backend/app/modules/ksl/fallback.py` is avatar, then video, then captions, then a person.

## `/ksl/clip`

`backend/app/main.py` mounts the KSL router at `/api/v1`. `GET /api/v1/ksl/clip/{template_id}` calls `registry.serve`. The id is a template id, not a file name and not a dataset word. Staff list and review routes are under `/api/v1/ksl/clips`.

## Production mode

`registry.production_mode` is true only when the caller passes `True`, or when the environment variable `CARELOOP_ENV` is `production` (any capitalisation). There is no research flag, no dataset config, and no dev-only route.

## What research samples must not touch

These surfaces are the patient and production paths. A later research module must not be imported here:

- `backend/app/modules/ksl/registry.py` and `router.py` (`/ksl/clip`)
- `backend/app/modules/ksl/manifest.py` and `config/ksl_phrase_manifest.yaml`
- `backend/app/modules/followup/` including `telegram.py`
- `frontend/src/app/enter/EnterFlow.tsx` and `frontend/src/ksl/SigningAvatar.tsx`

`scripts/check_ksl_assets.py` already rejects raw video, raw mocap, signer photos, and large binaries. It does not yet know about a downloaded pose dataset. The dataset is not on disk in this audit.

## Gap this branch is allowed to fill

An open word-based pose dataset can be downloaded outside git, after a person verifies its licence, and played only as a labelled research sample. That importer, licence gate, and research page do not exist yet.
