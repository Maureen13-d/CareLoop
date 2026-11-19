# Clinical Review Brief

> **Status: UNREVIEWED.** No clinician has reviewed anything below. Every number is a placeholder
> chosen by engineers. Time needed: about 20 minutes. No software knowledge required.

## What CareLoop is
CareLoop is a hackathon prototype that tracks people through the cervical screening-to-treatment
pathway. When someone is overdue at a stage, it sends escalating reminders (SMS, phone call,
community health worker visit; all **simulated**) and hands the case to a care coordinator if those
fail. It uses **synthetic data only**: no real patient or contact details exist anywhere in the
project. It is not a medical device and is not for clinical use.

## What we are asking
Tell us where the pathway, timeframes, contact ladder or message wording are **wrong, unsafe or
unrealistic**. You do not need guideline citations. "Too tight, in practice it is X" is the most
useful answer there is. Reply by question number; "OK" is a valid answer.

## What we are not asking
Approval for clinical use, regulatory or data-protection review, or anything about real patients.
**Please do not include real patient details in your reply.**

## 1. Current settings (generated from the code)

<!-- params:start -->
**A. Stages, timeframes and allowed transitions**

| Stage | Flagged overdue after (days) | Can move to |
|---|---|---|
| screened | 14 | abnormal result, closed |
| abnormal result | 7 | referred |
| referred | 30 | diagnostic done |
| diagnostic done | 14 | treatment started, closed |
| treatment started | 90 | closed |
| closed | n/a | (none, end of pathway) |

**B. Outreach ladder**

| Contact # | Channel |
|---|---|
| 1 | sms |
| 2 | call |
| 3 | home visit |
| 4 | hand-off to a care coordinator; automated outreach then stops |

Minimum gap between contacts: **3 days**. The ladder restarts when the case moves to a new stage.

**C. Message wording** (the same text is used for every reminder channel)

| Stage | Message |
|---|---|
| screened | A follow-up from your recent clinic visit is due. Please contact your clinic. |
| abnormal result | Your clinic has a follow-up appointment for you. Please call or visit the clinic this week. |
| referred | Reminder: your referral appointment is still pending. Please attend or call the clinic to reschedule. |
| diagnostic done | Your clinic has next steps to discuss with you. Please contact them to book a visit. |
| treatment started | Please remember to attend your scheduled clinic visits. |
<!-- params:end -->

## 2. Questions

### Pathway shape
1. The model is linear: screened, abnormal result, referred, diagnostic done, treatment started,
   closed. Does that match how a typical programme works? WHO describes more than one approach
   (for example screen-and-treat without a separate diagnostic step, and screen-triage-treat).
   Which route should this prototype represent?
2. A normal result closes the case immediately. Should it instead schedule a repeat screening?
   Or is closing correct for the scope of this tool?
3. After "diagnostic done" a case can close (no treatment needed) or move to treatment. What
   follow-up, if any, should happen before closing?
4. After "treatment started" the only next step is "closed". Should post-treatment follow-up be
   tracked?
5. Some patients need a different route (for example suspected invasive cancer, or women living
   with HIV, for whom WHO gives separate recommendations). Should the prototype exclude them, flag
   them, or handle them? Should suspected invasive cancer ever receive this automated ladder?
6. A case can only end at "closed". Do we need end states such as declined care, transferred,
   unreachable, or deceased? Without them reminders could keep going to someone who should not
   receive them.

### Timeframes
7. For each stage in table A: is the "flagged overdue after" number reasonable? Please give a
   number or say OK.
8. These numbers decide both when contact starts and what counts as "within target" in our
   metrics. Should those be two separate numbers (a clinical target versus a time to start chasing)?
9. Which of these depend on local conditions (distance, lab turnaround, referral capacity) and
   should therefore differ per site?

### Outreach ladder
10. Is SMS, then call, then community health worker visit, then care coordinator the right order?
    Is there anything that should never be automated or should always involve a person first?
11. Is a minimum gap of 3 days between contacts too frequent, too slow, or fine?
12. What must be true before contacting someone (consent, preferred contact method, a phone they
    can use safely, language)? Could a home visit ever cause harm (stigma, unwanted disclosure,
    personal safety)?
13. Should urgency change the ladder (for example skipping SMS for the most time-critical stages)?

### Message wording
14. Messages deliberately never name the condition, test or result, in case someone else reads the
    phone. Is that the right call? Is each message still clear enough that a patient would act?
15. The same text is used for SMS, call and visit. Should scripts differ by channel?
16. Could any message cause alarm, a misunderstanding, or false reassurance?

### Overall
17. Does anything here worry you from a patient-safety point of view, even if no question asks
    about it?
18. If you could change one thing before this goes anywhere near real patients, what would it be?

## 3. Reference points
- WHO guideline for screening and treatment of cervical pre-cancer lesions for cervical cancer
  prevention, second edition (2021): https://www.who.int/publications-detail-redirect/9789240030824
- WHO global strategy for cervical cancer elimination (90-70-90 targets):
  https://who.int/publications/i/item/9789240014107

These give programme-level targets and treatment algorithms. We have **not** found stage-by-stage
day limits in them, so the timeframes in table A cannot be justified by citing them. Please use
national or local programme guidance where it exists.

## 4. Reviewer response template
Reviewer role (optional; may be left anonymous):
Date:
Q1:
Q2:
... (one line per question; "OK" is fine)
Timeframes (stage: suggested days):
Biggest concern:

## 5. Sign-off record (maintainers complete after review)
| Field | Value |
|---|---|
| Reviewer role(s) | |
| Date(s) | |
| Documents the reviewer referred to | |
| Changes requested | |
| Changes made (PR link) | |
| Remaining caveats | |

## 6. When feedback arrives
1. Edit the values in `backend/app/pathway.py` and `backend/app/outreach.py`.
2. Run `python -m app.clinical_params --write` from `backend/`. The test suite fails until you do.
3. Update the disclaimer in `backend/app/metrics.py`, `docs/DATA_POLICY.md` and the README.
4. Complete the sign-off record above.

"Reviewed" must never be presented as "clinically validated": the data stays synthetic and the
project stays a prototype.
