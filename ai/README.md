# AI assets

Everything the assistant says or matches lives here as plain files, so people who are not developers can review and improve it.

| Folder | What it holds | Status |
|---|---|---|
| `lexicon/safety_en.yaml` | Phrases that signal crisis, distress, a request for a diagnosis, or a symptom report | DRAFT, needs clinical and language review |
| `lexicon/barriers_en.yaml` | Keywords and phrases for each barrier (fear, cost, transport, stigma, misconceptions, not knowing where to go, distress, lack of support), plus intents and the "What worries you most?" menu | DRAFT, needs language review |
| `templates/lite_en.yaml` | The approved replies Lite mode sends over USSD, SMS and web | DRAFT, needs clinical and language review |
| `knowledge/passages_en.yaml` | Approved passages for web chat, each with a source and review status | DRAFT, needs clinical review |

## Rules for every change

1. **Replies** must be plain ASCII, 160 characters or fewer, and must not use the words cancer, result, diagnosis, positive, hiv or screening. Phones are often shared. The tests enforce this.
2. **Replies never diagnose, interpret a result, recommend treatment, or discourage assessment.**
3. Text that needs verified information (for example a helpline) is marked `placeholder: true` and contains a visible bracket such as `[VERIFIED HELPLINE]`. Do not invent phone numbers.
4. Anything new needs a reviewer before it is described as reviewed. Until then it stays "draft".
5. Run `pytest` from the `backend` folder after changing any file here.

## How to extend

- **A new keyword or phrase:** add it to the right list. Phrases are worth three points, keywords one, and a flag needs three.
- **A new barrier:** add an entry under `flags:` in the barriers lexicon, add a `lite.barrier.<name>` template, and the tests will tell you if anything is missing.
- **A new language:** copy the three files with a new language suffix, get a fluent reviewer, and add the language to the assistant contract.
- **A knowledge base for web chat:** add a `kb/` folder with one file per passage, each naming its source and review status.

Matching never makes a medical judgement. It only decides which approved message to send and whether a human should step in.
