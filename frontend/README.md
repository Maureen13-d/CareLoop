# CareLoop web app

Next.js 16 (App Router, cache components), React 19, TypeScript and Tailwind CSS 4. All data comes from the FastAPI backend in `../backend`. Every person in it is synthetic.

## Run it

Start the backend first (see `../backend/README.md`), then:

```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
```

If the API is not on `http://localhost:8000`, set `NEXT_PUBLIC_API_URL`.

Sign in by picking a demo account on the sign-in page. The navigator, community health promoter and patient are shown first; the clinician, counsellor, program manager and admin are under **Other demo roles**. Every account uses the password `careloop-demo`.

## Check it

```bash
npm run lint
npm run build        # works offline: the font is self-hosted
npm start            # serve the production build
```

## What to try

| Account | Try this |
|---|---|
| David Kamau (clinician, under Other demo roles) | **Issue an ID card**, then print the card. **Open a case**, then claim it and move it on. **Arrivals**: record an arrival. |
| Amina Otieno (navigator) | **Today**, **Escalated cases** (what the guide handed over), **Cases** (search and filters), **Who to chase** (escalate, save an outcome), **Follow-up ladder** (run a sweep). The chat and the other patient channels are on the patient account. |
| Grace Achieng (community health promoter) | **Today** lists her women. Open one to record a home check. |
| Peter Omondi (program manager, under Other demo roles) | Counts, recent activity and the **Audit trail**. No names or chats. |
| Aisha Demo (patient) | **Support chat**, **Basic phone**, **Telegram**, **Voice**, **Cuff hub** and **Sign language**. Staff do not see these. |
| I have a card (on the sign-in page) | Enter an ID issued above. In this demo the code is shown on screen. |

## Where things live

| Path | What |
|---|---|
| `src/app/(app)/` | Signed-in pages. Each page checks the role on the server |
| `src/app/login`, `src/app/enter` | Sign-in and the patient's card entry |
| `src/components/ui/` | The design system. See `../docs/FRONTEND_DESIGN_SYSTEM.md` |
| `src/components/` | App-level pieces: shell, navigation, task item, pathway chart |
| `src/lib/` | API clients, session, display formatting, shared response types |
