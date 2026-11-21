# Traceability

Feature commits on `feat/screening-to-care-loop`. Search with `git log --grep "Feature: F07"`.

| Feature | Title | Status | Commits | Tests | Files |
|---|---|---|---|---|---|
| F00 | Audit | done | a6af705 | suite on the base: 254 passed | docs/AUDIT_V2.md |
| F01 | Repo hygiene | done | bdfe089 | scripts/test.ps1 | .gitignore, .env.example, scripts/test.ps1, README.md |
| F02 | Patient ID and slip | done | 2d48c2c | backend/tests/test_followup_loop.py | backend/app/modules/followup/register.py, ids.py, vault.py, models.py |
| F03 | Second check | done | 6ba7a7d | backend/tests/test_followup_loop.py | backend/app/modules/followup/access.py |
| F04 | Pseudonymisation note | done | 16cb070 | contact is not on the slip or the dashboard | docs/DATA_GOVERNANCE.md, vault.py |
| F05 | Journey model | done | 3c7f253 | backend/tests/test_followup_pathway.py | pathways/follow_up.yaml |
| F06 | Facility dashboard | done | a93fab5, c835536 | backend/tests/test_followup_loop.py | facility.py, frontend/src/app/(app)/facility |
| F07 | CHW worklist | done | f098922, 353e2ef, c835536 | test_followup_loop.py, test_workspace.py | worklist.py, workspace_seed.py, frontend worklist |
| F08 | Patient card | done | c835536 | spoken text asserted in test_followup_loop.py | frontend/src/app/enter |
| F09 | Conversation core | done | db33c7e | backend/tests/test_followup_loop.py | conversation.py, ai/templates/followup.yaml |
| F10 | Check-in scheduler | done | aca302a | backend/tests/test_followup_loop.py | checkins.py, config/followup_checkins.yaml |
| F11 | Telegram | done | 1c3ddce, c835536 | backend/tests/test_followup_loop.py | telegram.py, frontend/src/app/(app)/telegram |
| F12 | USSD contract | done | 7a68efa | ussd route in test_followup_loop.py | docs/USSD_CONTRACT.md |
| F13 | Guide | done | c835536 | guide_speaks in test_followup_loop.py | frontend/src/app/enter/EnterFlow.tsx |
| F14 | Safety checks | done | 1ea2ca4 | backend/tests/test_followup_loop.py | router.py and the safety test |
| F15 | Cohort and eval | done | a3bae29 | backend/tests/test_followup_loop.py | cohort.py, ai/eval/followup_test.jsonl |
| F16 | Submission docs | done | f0dede9 | n/a | docs/SUBMISSION.md, docs/LIMITATIONS.md, docs/DATA_DECLARATION.md |
| F17 | Final verification | partial | not tagged submission-ready | 265 passed on this branch | browser walkthrough of the demo script was not run |

Maternal and hardware files were not changed except the one pathway-engine guard that keeps the CHW pregnancy check on maternal cases only (`3c7f253`).
