# Telegram Mini App (specification only)

Not built. If it is built later, it is a view, not a second brain.

## Job

Show the same journey map the bot already sends: Seen, In touch, Clinic visit, Clinic. Later it could show the signing avatar. It must not collect a diagnosis, a photo of a result, or a free-text clinical note.

## Trust

- The page loads inside Telegram and receives `initData`.
- The API checks the hash with the bot token using Telegram's documented algorithm before it trusts the user.
- Reject expired `auth_date` values. Reject any payload whose hash does not match.
- The Patient ID is not taken from the query string. The chat is already bound in `telegram_vault`.
- Do not put the Patient ID, the chat id, or the bot token in the page URL.

## Limits

- Same approved lines as `config/templates/telegram.en.yaml` and `telegram.sw.yaml`.
- No map of the person's location. The clinic list stays the synthetic demo list until a reviewed directory exists.
- Arrival is still confirmed by facility staff.
