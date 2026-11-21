import { redirect } from "next/navigation";
import { Banner, Notice } from "@/components/ui";
import { getSession } from "@/lib/session";
import { registerScreening } from "./actions";

export const instant = false;

const field = "mt-1 w-full rounded-xl border border-line bg-white px-3 py-3 text-base";

export default async function ScreenPage({
  searchParams,
}: {
  searchParams: Promise<{ notice?: string; error?: string }>;
}) {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role !== "clinician") redirect("/");
  const { notice, error } = await searchParams;

  return (
    <main className="mx-auto max-w-xl space-y-6 px-4 py-6">
      <header>
        <p className="text-sm text-lagoon">SYNTHETIC · PENDING CLINICAL REVIEW</p>
        <h1 className="mt-1 text-4xl">Record a screening</h1>
        <p className="mt-2 text-ink-soft">
          A concerning or urgent finding, with consent, opens follow-up and issues an ID. The
          contact is stored apart from the card.
        </p>
      </header>
      <Banner>Synthetic demo only. Do not type a real phone number.</Banner>
      {notice ? <Notice tone="ok">Saved. Status: {notice}</Notice> : null}
      {error ? <Notice tone="bad">{error}</Notice> : null}
      <form action={registerScreening} className="space-y-4 rounded-2xl border border-line bg-paper-2 p-5">
        <label className="block text-sm">
          Age band
          <select name="age_band" className={field} defaultValue="30-34">
            <option>20-24</option>
            <option>25-29</option>
            <option>30-34</option>
            <option>35-39</option>
            <option>40-44</option>
          </select>
        </label>
        <label className="block text-sm">
          Area label
          <input name="area_label" required className={field} defaultValue="Demo Zone A" />
        </label>
        <label className="block text-sm">
          Screening type
          <select name="screening_type" className={field} defaultValue="general">
            <option value="general">General</option>
            <option value="cervical">Cervical</option>
            <option value="blood_pressure">Blood pressure</option>
            <option value="hiv">HIV</option>
            <option value="tb">TB</option>
          </select>
        </label>
        <label className="block text-sm">
          Finding
          <select name="finding" className={field} defaultValue="concerning">
            <option value="concerning">Concerning</option>
            <option value="urgent">Urgent</option>
            <option value="not_concerning">Not concerning</option>
            <option value="inadequate">Inadequate</option>
          </select>
        </label>
        <label className="block text-sm">
          Language
          <select name="language" className={field} defaultValue="en">
            <option value="en">English</option>
            <option value="sw">Kiswahili</option>
          </select>
        </label>
        <label className="block text-sm">
          Preferred channel
          <select name="channel" className={field} defaultValue="telegram">
            <option value="telegram">Telegram</option>
            <option value="sms">SMS</option>
            <option value="ussd">USSD</option>
            <option value="web">Web</option>
            <option value="voice">Voice</option>
          </select>
        </label>
        <label className="block text-sm">
          Contact (not printed on the card)
          <input name="contact" className={field} placeholder="07…" />
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" name="consent" defaultChecked className="h-5 w-5" />
          Consent to follow-up
        </label>
        <button className="min-h-12 w-full rounded-full bg-lagoon px-4 text-white" type="submit">
          Issue ID
        </button>
      </form>
    </main>
  );
}
