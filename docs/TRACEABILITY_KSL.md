# KSL traceability

Feature commits on `feat/ksl-avatar`. Search with `git log --grep "Feature: K00"`.

There is no `ksl-ready` tag. No approved Kenyan Sign Language clip exists, so a tag would overclaim the content.

| Feature | Title | Status | Commits | Tests | Files |
|---|---|---|---|---|---|
| K00 | Audit and plan | done | e53e9bf | none (docs only) | docs/AUDIT_KSL.md |
| K01 | Asset policy | done | 9c7494f, 8a9d98d | scripts/test_ksl_asset_policy.py | .gitignore, .gitattributes, scripts/check_ksl_assets.py, .github/workflows/ci.yml |
| K02 | Motion packet spec | done | 7012164 | backend/tests/test_ksl_kmp.py | backend/app/modules/ksl/kmp.py, docs/KMP_SPEC.md, schemas/kmp-1.schema.json, assets/ksl/placeholders/test_motion.json |
| K03 | Clip tables and manifest | done | 6ac61eb | backend/tests/test_ksl_manifest.py | backend/app/modules/ksl/models.py, manifest.py, config/ksl_phrase_manifest.yaml |
| K04 | Clip registry API | done | bfb2634, 146143a | backend/tests/test_ksl_registry.py | backend/app/modules/ksl/registry.py, router.py |
| K05 | Review workflow | done | 243cebe, 146143a | backend/tests/test_ksl_registry.py | backend/app/modules/ksl/review.py, router.py |
| K06 | Avatar rig | partial | 1fdb5ad | none (joint names only) | assets/ksl/rig/guide.gltf |
| K07 | Playback | done | 7b90eab | frontend/src/ksl/engine.test.js | frontend/src/ksl/engine.js, SigningAvatar.tsx |
| K08 | Non-manual channels | done | 7b90eab | frontend/src/ksl/engine.test.js | frontend/src/ksl/engine.js |
| K09 | Idle and attention | done | 7b90eab | frontend/src/ksl/engine.test.js | frontend/src/ksl/engine.js |
| K10 | Appearance presets | done | 7b90eab | frontend/src/ksl/engine.test.js | frontend/src/ksl/engine.js |
| K11 | Fallback ladder | done | 7b90eab | frontend/src/ksl/engine.test.js, backend/tests/test_ksl_followup.py | frontend/src/ksl/engine.js, backend/app/modules/ksl/fallback.py |
| K12 | Core integration | done | 2c7312d, 146143a | backend/tests/test_ksl_followup.py | backend/app/modules/followup/conversation.py, ai/templates/followup.yaml |
| K13 | Telegram video | done | bfb2634, 146143a | backend/tests/test_ksl_followup.py | backend/app/modules/ksl/registry.py |
| K14 | Deaf-aware follow-up | done | a8fbdb9 | backend/tests/test_ksl_followup.py | checkins.py, worklist.py, config/followup_checkins.yaml |
| K15 | Guided call | done | 146143a | backend/tests/test_ksl_followup.py | backend/app/modules/ksl/guided.py, router.py, frontend/src/app/enter/EnterFlow.tsx |
| K16 | Docs | done | 20907ee | none (docs only) | docs/KSL_DESIGN.md, KSL_DATA_PLAN.md, CONSENT_OUTLINE.md, VALIDATION_PROTOCOL.md, DEMO_SCRIPT_KSL.md, LIMITATIONS.md |
| K17 | Tag ksl-ready | not tagged | | backend KSL tests and frontend/src/ksl/engine.test.js were run locally | .github/workflows/ci.yml |
