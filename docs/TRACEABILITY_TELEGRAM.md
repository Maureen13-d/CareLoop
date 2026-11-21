# Telegram traceability

Branch `feat/telegram-bot`, cut from `feat/ksl-avatar` at `aa89055`. Search with `git log --grep "Feature: T06"`.

T03 through T14 share one engine, so they landed in `73cffd6`. The docs and the staff simulator landed in `dbb41f5`.

| Feature | Title | Status | Commits | Tests | Files |
|---|---|---|---|---|---|
| T00 | Audit | done | 9fedb55 | none | docs/AUDIT_TELEGRAM.md |
| T01 | Config and secrets | done | 63ae548 | backend/tests/test_telegram_env.py | telegram_env.py, .env.example |
| T02 | Flow config and copy | done | a72bec4 | backend/tests/test_telegram_bot.py | config/telegram_flows.yaml, config/templates/telegram.*.yaml, telegram_copy.py |
| T03 | Webhook, dedupe, polling | done | 73cffd6 | backend/tests/test_telegram_bot.py | telegram.py |
| T04 | Main menu | done | 73cffd6 | backend/tests/test_telegram_bot.py | telegram_flow.py |
| T05 | Deep link and binding | done | 73cffd6 | backend/tests/test_telegram_bot.py | telegram_models.py, telegram_flow.py |
| T06 | Check-in inside the bot | done | 73cffd6 | backend/tests/test_telegram_bot.py | checkins.py, telegram.py |
| T07 | Find a clinic | done | 73cffd6 | backend/tests/test_telegram_bot.py | config/telegram_clinics.yaml |
| T08 | I need help | done | 73cffd6 | backend/tests/test_telegram_bot.py | telegram_flow.py |
| T09 | Visit questions | done | 73cffd6 | backend/tests/test_telegram_bot.py | telegram.en.yaml, telegram.sw.yaml |
| T10 | Outbound, 429, blocked bot | done | 73cffd6 | backend/tests/test_telegram_bot.py | telegram.py |
| T11 | Settings and removal | done | 73cffd6 | backend/tests/test_telegram_bot.py | telegram_flow.py |
| T12 | Simulator shows the same menus | done | 73cffd6, dbb41f5 | backend/tests/test_telegram_bot.py | telegram.py, frontend TelegramSim.tsx |
| T13 | KSL send or a task | done | 73cffd6 | backend/tests/test_telegram_bot.py | telegram.py |
| T14 | Optional tips | done | 73cffd6 | backend/tests/test_telegram_bot.py | telegram_flow.py |
| T15 | Mini App specification only | done | dbb41f5 | none | docs/TELEGRAM_MINI_APP.md |
| T16 | Docs, demo, limitations | done | dbb41f5 | none | docs/TELEGRAM_BOT.md, docs/TELEGRAM_COPY.md, docs/DEMO_SCRIPT_TELEGRAM.md, docs/LIMITATIONS.md |

## Decisions

- The chat id lives in `telegram_vault`, not in the phone contact vault, so a Telegram bind does not erase a phone number.
- The deep link is spent when the ID and the code succeed, not when `/start` arrives, so a stranger cannot burn it.
- A Telegram slip QR opens the bot link. Other channels still use the Patient ID on the slip.
- `present()` skips a blank name and then reads the older `CARELOOP_` alias. `setting()` stays strict.
- Not sure opens one urgent task and is not stored as worse.
- Ordinary unclear text returns the menu and does not open a task. Worse, not sure, danger, and a confirmed barrier do.
- Fly still runs the earlier adapter until this branch is deployed on its own. Do not deploy while unrelated facility files are in the working tree.
