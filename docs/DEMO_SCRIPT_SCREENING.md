# Four-minute demo: from a screening to an arrival

Synthetic data only. Log in with password `careloop-demo`. Delete `backend/careloop.db` before the first run so Grace's follow-up IDs exist.

The maternal story in `docs/DEMO_SCRIPT.md` is a different pathway. This is the screening story.

## 0:00 Clinician issues an ID

Sign in as **david**. Open **Screen**. Record a concerning finding, tick consent, and add a fake contact. Submit.

The slip shows an ID, a QR of that ID only, and three plain lines. It does not name a condition. It does not show the contact.

## 0:45 The card, day 3, a fare barrier

Open **I have a card** (`/enter`). Enter the ID. The simulated code appears because this is a prototype. Enter it.

The guide says the next step is the clinic. It is a guide, not a doctor. Ask "not yet", then "transport". The reply offers help with fare. It does not say the person is fine.

The admin clock can move the demo to day 3 (`POST /api/v1/admin/advance-clock`). Check-ins are every two days, skip quiet hours, and stop after STOP.

## 2:00 Day 5, worse, the worklist

On the card, choose "I feel worse". The screen says to go to the nearest clinic now, with no extra animation. One urgent task is opened.

Sign in as **grace**. Open **Chase**. The worse row is first. The reason is "reported worse symptoms". The recommended action is "escalate to clinician". Escalate once. A second tap does not open a second task.

Other rows show reasons such as "not arrived, 9 days" or "barrier: transport fare".

## 3:00 The clinic confirms arrival

Sign in as **david**. Open **Arrivals**. Record arrival for that ID. The state becomes `arrived`. The person drops off the chase list. Lost to follow-up stays in its own queue until a person decides, and only if an escalation already exists.

## 3:30 The numbers

Arrivals shows the funnel, the percent arrived, and the median time from screening to arrival. The note on the page says this is not a causal comparison: outreach starts because the visit is already late. A 200-person synthetic cohort is available to an admin at `POST /api/v1/followup/cohort`.

## If a step fails

Say so. Do not invent a result. The limitations are in `docs/LIMITATIONS.md`.
