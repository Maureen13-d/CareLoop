# Telegram bot

The bot is an adapter. It turns a Telegram update into a call on the conversation core, then renders an approved line. It does not invent medical answers.

```
Telegram update
    -> secret check, dedupe by update_id
    -> Telegram adapter
    -> conversation core (safety first)
    -> journey, tasks, check-ins
    -> reply keyboard or inline buttons
```

## What is real, simulated, and not built

- Real: menus, deep-link tokens, the contact vault, check-in rules, tasks, and the webhook contract.
- Simulated: the one-time code, the clinic list, and facility hours.
- Not built: WhatsApp, a trained sign recogniser, and a Telegram Mini App (specified only in `docs/TELEGRAM_MINI_APP.md`).

## Environment

Placeholders live in `.env.example`. Real values stay in `backend/.env` or the host secret store. Never commit them.

| Name | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot API token |
| `TELEGRAM_WEBHOOK_SECRET` | `secret_token` from `setWebhook`. Characters `A-Z a-z 0-9 _ -` only. |
| `TELEGRAM_BOT_USERNAME` | Used in the slip deep link. Default `LoopieCareBot`. |
| `PUBLIC_BASE_URL` | Public origin of this API. |

Older deploys may still set `CARELOOP_TELEGRAM_BOT_TOKEN` and `CARELOOP_TELEGRAM_WEBHOOK_SECRET`. Those are accepted when the names above are empty.

## Webhook

`POST /api/v1/followup/telegram/webhook`

Telegram sends `X-Telegram-Bot-Api-Secret-Token`. A missing or wrong secret is rejected. The same `update_id` is handled once.

Checked against the Bot API on 21 Nov 2026:

- `callback_data` is limited to 64 bytes. Buttons use short codes, never a Patient ID.
- A deep-link payload is at most 64 characters and may contain only `A-Z a-z 0-9 _ -`.
- A bot can delete an incoming private message from the last 48 hours. The adapter asks Telegram to delete the message that carried the ID.
- `setMyCommands` takes an optional `language_code`.
- `sendChatAction` lasts about 5 seconds.
- A 429 can include `retry_after`. The sender tries once more.
- While a webhook is set, `getUpdates` does not deliver updates.

Register the webhook only after the API is on HTTPS:

```
https://api.telegram.org/bot<token>/setWebhook
url = PUBLIC_BASE_URL/api/v1/followup/telegram/webhook
secret_token = TELEGRAM_WEBHOOK_SECRET
allowed_updates = ["message", "edited_message", "callback_query"]
```

## Local polling

Use polling only on a machine that does not have a webhook set. Call `poll_once` from a shell. Do not run it in production beside the webhook.

## Patient path

1. The slip QR for a Telegram enrolment opens `https://t.me/<bot>?start=<token>`. The token is random, single-use, and expires. It is not the Patient ID.
2. Language, then a short privacy line, then the ID, then the one-time code.
3. The chat id is stored only on `telegram_vault`.
4. The menu is My next step, Find a clinic, I need help, What happens at a visit, Language, and Settings.
5. Check-ins follow the existing cadence, quiet hours, and cap. They are sent only after the person has opened the bot. Pause, STOP, and Remove me stop that.

STOP unbinds the chat. START asks for the ID and the code again. A patient saying they have been does not close the case. Worse and Not sure open one urgent task and use a plain line with no emoji.

## Commands

`/start` `/menu` `/status` `/help` `/language` `/stop`

Descriptions are registered in English and Kiswahili through `setMyCommands`.

## Copy

Strings live in `config/templates/telegram.en.yaml` and `config/templates/telegram.sw.yaml`. Both are `PENDING CLINICAL REVIEW`. Kiswahili is `swahili_review: pending`. The review deck is `docs/TELEGRAM_COPY.md`.
