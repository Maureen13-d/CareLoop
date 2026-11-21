# Four-minute demo

Synthetic data only. Delete `backend/careloop.db` before the first run so Grace, Mercy, and hub HUB-0007 exist. Password for every person: `careloop-demo`. No Docker.

Start three processes:

1. API on port 8000, from `backend/`: `.venv/Scripts/python -m uvicorn app.main:app --port 8000`
2. Web on port 3000, from `frontend/`: `npm run dev`
3. Simulated clinic on port 8100, from the repository root: `backend/.venv/Scripts/python -m uvicorn integrations.mock_hospital.app:app --port 8100`

## 0:00 Grace and Mercy

Sign in as **grace**. Today lists only her women. Open **Mercy Demo**. Say that a colour is a label for a person, not a diagnosis, and that the rules are pending clinical review.

Record a cuff reading: systolic 152, diastolic 98, urine `2+`, haemoglobin `normal`, and both severe head pain and blurred vision. The server label is red. The journey moves to "needs a person" with the shorter assumed deadline. The audit does not store a sentence Mercy said.

## 1:00 The hub, offline, then a duplicate

Open **Hub**. Choose Mercy's booklet. Set a high reading and turn the link to **Offline**. Send. The lamps show a word as well as a state, and the reading stays queued. Switch to **Data** and send the queue. Send the same reading again. The server says the duplicate was ignored.

## 2:00 Amina

Sign in as **amina**. Today shows the maternal red count and a countdown. Open Mercy. Note the fare barrier, request the simulated voucher, and record a cover check. The voucher says `SIMULATED_MPESA` and `assumed`. The cover check says `SIMULATED_SHA`. Approve is a navigator step. Grace cannot approve it.

Move the journey to navigating if it is not there yet, then **Send the visit request**. The pretend clinic accepts it and the state becomes visit booked. Record the clinic's next milestones until the state is "with the hospital". The milestone names are arrived, antenatal visit completed, and care plan recorded. If port 8100 is down, the card says the simulated clinic is not running.

## 3:20 Peter

Sign in as **peter**. The maternal counts are visible. Open **Audit**. The new rows are action names and labels such as the level and the template id. They do not contain a free-text note from Mercy.

Optional, if there is time: on the phone simulator, dial the placeholder `*XYZ#` and send `M` for the maternal check-in. The ordinary menu still starts with "1 Next step". A red reply tells her to go to the nearest clinic and does not name a condition.
