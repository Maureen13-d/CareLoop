# Telegram audit (T00)

Audited on 21 Nov 2026 from `feat/ksl-avatar` at `aa89055`. No bot behaviour was changed for this note. `main` and the tag `p0-complete` were not moved.

## What is already on this branch

The follow-up Telegram path is a thin adapter around the conversation core.

| Piece | Where | What it does |
|---|---|---|
| Webhook | `POST /api/v1/followup/telegram/webhook` | Requires `X-Telegram-Bot-Api-Secret-Token` to match `CARELOOP_TELEGRAM_WEBHOOK_SECRET`. A missing or wrong secret is rejected. |
| Simulator | `POST /api/v1/followup/telegram/simulate` and `/telegram` | Staff type a line. The page says it is not a real Telegram account. |
| Core | `conversation.handle` | Safety lexicon first, then language, Patient ID, one-time code, then the fixed menu. |
| Session | `followup_sessions` | One row per channel and session key. The last `update_id` is stored and a repeat is ignored. |
| Vault | `contact_vault` | One contact string per Patient ID, written at registration. Dashboards are not supposed to read it. |
| Check-ins | `checkins.run_checkins` | Every 48 hours, quiet hours 21:00–07:00, six attempts, a task after three misses (one miss for KSL). The text is logged. It is not sent to Telegram. |
| Copy | `ai/templates/followup.yaml` | English and Kiswahili lines. KSL falls back to captions and can open a human task. |

The core reply is a dict: `reply_text`, `quick_replies`, `actions`, `escalation_label`, `template_id`, and a `ksl` packet (`available`, `fallback`, `caption`). The adapter today returns the text. It does not draw buttons, and it does not send a video.

## What is only in the working tree

These edits are not committed and are not part of T00:

- The webhook accepts a real Telegram Update as well as the simulator body, and can call `sendMessage` when a token is set.
- After a valid ID, a prototype build can append the simulated one-time code to the reply.
- A token and webhook secret sit in `backend/.env`, which git ignores. The same names were set as Fly secrets for `careloop-screening-api`. They are not in git.

That working copy still has no menus, no deep link, no callback buttons, and no unreachable handling.

## Gaps against the bot we are building

- There is no flow file and no Telegram template pack. Buttons in the core are labels, not a Telegram keyboard.
- The Patient ID and the code are typed into the same chat. The bot does not delete the ID message. A deep-link token does not exist, so the ID slip QR cannot open a bound chat.
- `chat_id` is the session key on `followup_sessions`. That table is not the contact vault. The vault stores whatever contact was typed at registration, which may be a phone number rather than a Telegram chat.
- STOP sets `messages_stopped` on the enrolment. It does not unbind a chat. START resumes the same session without a new code check.
- Check-ins never call Telegram. A blocked bot is not detected, and no "try another channel" task is opened.
- The simulator and the webhook both call `ingest`, but the page is a text box. It does not render the same buttons the real bot will use.
- Outbound rows store the message body. The audit log stores labels. A simulated code in a reply would therefore land in `followup_outbound`, not in the audit log.
- Nothing in the bot says that a Telegram chat with a bot is not end-to-end encrypted.

## Bot API, checked on 21 Nov 2026

Checked [core.telegram.org/bots/api](https://core.telegram.org/bots/api) and [core.telegram.org/bots/features](https://core.telegram.org/bots/features). Differences from the prompt are noted here so later features do not guess.

| Feature | What the current docs say |
|---|---|
| Webhook secret | `secret_token` may contain only `A-Z`, `a-z`, `0-9`, `_` and `-`. Telegram sends it as `X-Telegram-Bot-Api-Secret-Token`. While a webhook is set, `getUpdates` does not deliver updates. |
| Delete a message | `deleteMessage`: a bot can delete an incoming message in a private chat. A message can only be deleted if it was sent less than 48 hours ago. |
| Buttons | `callback_data` is 1–64 bytes. The docs do not allow a longer payload. |
| Deep link | `https://t.me/<bot>?start=<payload>`. The payload is at most 64 characters and may contain only `A-Z`, `a-z`, `0-9`, `_` and `-`. The bot receives `/start <payload>`. |
| Commands | `setMyCommands` accepts at most 100 commands and an optional `language_code` (ISO 639-1). |
| Typing | `sendChatAction` shows a status for 5 seconds or less. |
| Flood control | A 429 response can include `retry_after` (seconds). |
| Mini App | Documented as a later interface. Not used here. |

The docs do not say that a chat with a bot is end-to-end encrypted. Secret chats are a separate Telegram feature and are not available to bots. Later copy must say that plainly and must not promise secrecy.

Error text for "bot was blocked" and "chat not found" was not pinned in this audit. T10 will match those failures from recorded API responses, not from a guessed sentence.

## Decision this audit does not make

The canonical environment names in the build prompt are `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `TELEGRAM_BOT_USERNAME`, and `PUBLIC_BASE_URL`. The code on this branch still reads `CARELOOP_TELEGRAM_BOT_TOKEN` and `CARELOOP_TELEGRAM_WEBHOOK_SECRET`. T01 records both and does not put a real value in git.
