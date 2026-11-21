# KSL research traceability

Branch `feat/ksl-research-mode`, cut from `feat/ksl-avatar` at `aa89055`. Search with `git log --grep "Feature: R00"`.

`ksl_dataset.license_verified` is true after the owner's check on 21 Nov 2026. The dataset is not in git. The public zip was indexed by range request and was not saved.

| Feature | Title | Status | Commits | Tests | Files |
|---|---|---|---|---|---|
| R00 | Audit | done | 6bd508a | none | docs/AUDIT_KSL_RESEARCH.md |
| R01 | Licence gate and download script | done | f085b0d | backend/tests/test_ksl_research_policy.py, scripts/test_ksl_asset_policy.py, frontend/src/ksl/researchLabel.test.js | config/ksl_dataset.yaml, scripts/fetch_ksl_dataset.py, backend/app/modules/ksl/research/, docs/DATASET_ATTRIBUTION.md, docs/DATASET_LICENSE_CHECK.md |
| R02 | Inspect the data | done | 6c880c8, 700de75 | scripts/test_ksl_dataset_index.py | scripts/ksl_dataset_index.py, scripts/inspect_ksl_dataset.py, docs/KSL_DATASET_INSPECTION.md |
| R03 | Vocabulary report | done | a906bd5 | scripts/test_ksl_dataset_index.py | docs/KSL_VOCAB_REPORT.md |
| R04 | Normalize landmarks | done | 1917b57 | scripts/test_ksl_dataset_index.py | scripts/ksl_dataset_index.py, backend/app/modules/ksl/research/normalize.py |
| R05 | Retarget to the avatar | done | 481cbc7 | backend/tests/test_ksl_research_motion.py | backend/app/modules/ksl/research/retarget.py, backend/app/modules/ksl/research/overlay.py, docs/KSL_RETARGETING.md |
| R06 | Research sample page | done | e9fa8a9 | backend/tests/test_ksl_research_motion.py, frontend/src/ksl/researchPose.test.js | backend/app/modules/ksl/research/router.py, frontend/src/app/dev/ksl-research/page.tsx |
| R07 | Demo pre-render | not started | | | |
| R08 | Offline recognizer experiment | not started | | | |
| R09 | Honesty docs | not started | | | |
| R10 | Final verification | not started | | | |

## Decisions

- The licence flag is read only from `config/ksl_dataset.yaml`. An environment variable cannot turn research mode on.
- The importer accepts the checksum Zenodo publishes. For this file that is an md5, not a sha256. A download still needs `--download` and enough free disk.
- The cited record `14974973` is restricted. Inspection used the open version `14338329`.
- Recording-folder numbers are not treated as signer ids. The archive does not say that.
- Pickled `.npy` files are not loaded by the app or the download script.
- The attribution footer exists for later research views. No patient page imports it.
- A research packet stores `fps` as empty. Playback at 12 frames per second is a display choice. The archive does not record a frame rate.
- The one converted word, PAIN from Batch 1 folder 205, stays in `data/external/` and is not committed.
- `/dev/ksl-research` answers only when the licence flag is on and `CARELOOP_ENV` is dev, demo, test, or unset. Production returns 404.
