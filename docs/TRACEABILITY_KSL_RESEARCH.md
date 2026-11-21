# KSL research traceability

Branch `feat/ksl-research-mode`, cut from `feat/ksl-avatar` at `aa89055`. Search with `git log --grep "Feature: R00"`.

Research mode is off. `ksl_dataset.license_verified` is false. The dataset is not in git.

| Feature | Title | Status | Commits | Tests | Files |
|---|---|---|---|---|---|
| R00 | Audit | done | 6bd508a | none | docs/AUDIT_KSL_RESEARCH.md |
| R01 | Licence gate and download script | done | f085b0d | backend/tests/test_ksl_research_policy.py, scripts/test_ksl_asset_policy.py, frontend/src/ksl/researchLabel.test.js | config/ksl_dataset.yaml, scripts/fetch_ksl_dataset.py, backend/app/modules/ksl/research/, docs/DATASET_ATTRIBUTION.md, docs/DATASET_LICENSE_CHECK.md |
| R02 | Inspect the data | not started | | | |
| R03 | Vocabulary report | not started | | | |
| R04 | Normalize landmarks | not started | | | |
| R05 | Retarget to the avatar | not started | | | |
| R06 | Research sample page | not started | | | |
| R07 | Demo pre-render | not started | | | |
| R08 | Offline recognizer experiment | not started | | | |
| R09 | Honesty docs | not started | | | |
| R10 | Final verification | not started | | | |

## Decisions

- The licence flag is read only from `config/ksl_dataset.yaml`. An environment variable cannot turn research mode on.
- The importer also refuses to download until a sha256 from the Zenodo record is present. A checksum match is required before the archive is kept.
- Pickled `.npy` files are not loaded by the app or the download script.
- The attribution footer exists for later research views. No patient page imports it.
