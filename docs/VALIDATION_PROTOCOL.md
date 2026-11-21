# KSL validation protocol

Nothing in this build has been validated as Kenyan Sign Language. The protocol below is what has to happen before a clip is shown to a patient in a pilot.

## Before a clip can play

1. The line is one id in `config/ksl_phrase_manifest.yaml`. Free text is not accepted.
2. The signer has recorded consent and has not revoked it.
3. A Deaf reviewer with the `ksl_reviewer` role passes `deaf_review`.
4. A second Deaf reviewer passes `back_translation`. The same person cannot do both.
5. An admin or programme manager, who did not upload the clip and did not review it, confirms.
6. The stored hash still matches the current template line. A changed line marks the clip stale.
7. The label is not `TEST_MOTION_NOT_SIGN` or `PLACEHOLDER MOTION: NOT KSL` when `CARELOOP_ENV` is `production`.
8. `clinical_review` on the phrase is `reviewed`. Until then the clip can be approved in software and `pilot_enabled` stays false.

## What this build checks automatically

`backend/tests/test_ksl_registry.py` covers unapproved, stale, revoked, same-reviewer, uploader-as-approver, and the production block on the test label.

`backend/tests/test_ksl_followup.py` covers captions, the text-only channels, the first missed KSL check-in, the worklist actions, and one human task after a confirmed "worse".

`frontend/src/ksl/engine.test.js` covers timing, reduced motion, unsmoothed hands and face, and the fallback order.

## What is not claimed

No recognition accuracy. No phone frame rate. No clinical safety beyond the existing rule that worse and unclear replies escalate. A Deaf review team has not yet used the screen at `/ksl`.
