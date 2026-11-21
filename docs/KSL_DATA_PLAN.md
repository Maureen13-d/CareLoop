# KSL data plan

This is a plan for a later capture, not a claim that a dataset is in the repo.

## What this repository holds

- A phrase list of 40 fixed lines in `config/ksl_phrase_manifest.yaml`. IDs, dates, and clinic names are not slots inside a sign. They stay as text or pictograms beside the clip.
- A procedural wave at `assets/ksl/placeholders/test_motion.json`, labelled `TEST_MOTION_NOT_SIGN`.
- A joint-name glTF. No mesh of a person.

Raw video, raw motion capture, and signer photos are refused by `scripts/check_ksl_assets.py`. Approved rendered packs, if they ever exist, belong under `assets/ksl/approved/` as Git LFS pointers.

## What a real capture would need

Landmarks would be computed on the device that records. The original camera file would not be committed. A signer is stored as a pseudonym. Revoking consent retires every clip from that signer.

Each clip stores a hash of the template line it was recorded against. If the line changes, the clip is marked stale and is not served.

## What this plan does not assume

Public KSL collections, including numbers cited for AI4KSL, a Data in Brief paper, or a 2026 workshop, were not checked for this build. Their sizes, licences, and whether they allow a clinical avatar are unverified. Do not treat those figures as permission.

American Sign Language is not Kenyan Sign Language. A model or clip from one cannot be labelled as the other.

No partner, including any avatar vendor, is implied by this repository.
