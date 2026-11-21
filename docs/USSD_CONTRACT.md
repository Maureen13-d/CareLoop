# USSD contract

This is the shape a gateway calls. It is **not** Africa's Talking's payload. Do not guess their field names. When that connection is built, map their body onto this contract in one place.

## Request

`POST /api/v1/followup/ussd`

```json
{
  "chat_id": "session-id-from-the-gateway",
  "text": "1",
  "update_id": null
}
```

- `chat_id` is the gateway session id, or a phone reference if that is all the gateway has. It is not printed on the ID card.
- `text` is the latest menu choice or the text the person sent. Empty text asks for the language.
- The route does not implement a provider signature. The gateway team adds that when the provider is chosen.

## Response

```json
{
  "text": "CareLoop\n1 English\n2 Kiswahili",
  "continue_session": true,
  "synthetic": true
}
```

- `text` is at most 182 characters.
- `continue_session` false means the gateway should end the session. A danger-sign reply ends it.
- The words come from the same conversation core as web and Telegram.

The existing phone simulator at `/phone` still runs the cervical and maternal menus. This contract is the follow-up menu.
