import { redirect } from "next/navigation";
import { recordFinding } from "./actions";
import { Banner, Notice } from "@/components/ui";
import { getSession } from "@/lib/session";

export const instant = false;

const field = "w-full rounded-xl border border-line bg-white px-3 py-2 text-sm";

export default async function IntakePage({
  searchParams,
}: {
  searchParams: Promise<{ notice?: string; error?: string }>;
}) {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role !== "clinician") redirect("/");
  const { notice, error } = await searchParams;

  return (
    <main className="mx-auto max-w-xl space-y-6 px-4 py-6 md:px-0 md:py-0">
      <header>
        <p className="text-sm text-lagoon">New finding</p>
        <h1 className="mt-1 text-4xl">Record a concerning check</h1>
        <p className="mt-2 text-ink-soft">
          This is not a diagnosis. With the person’s permission, a concerning finding opens a
          navigation case. Use a synthetic name.
        </p>
      </header>
      <Banner>Nothing on this form is a real patient. Do not type a real name or phone number.</Banner>
      {notice ? <Notice tone="ok">{notice}</Notice> : null}
      {error ? <Notice tone="bad">{error}</Notice> : null}
      <form action={recordFinding} className="space-y-4 rounded-2xl border border-line bg-paper-2 p-5">
        <label className="block text-sm">
          Synthetic name
          <input name="display_name" required minLength={2} className={`${field} mt-1`} placeholder="Demo Amina" />
        </label>
        <label className="block text-sm">
          Age band
          <select name="age_band" className={`${field} mt-1`} defaultValue="30-34">
            {["25-29", "30-34", "35-39", "40-44", "45-49", "50-54"].map((band) => (
              <option key={band}>{band}</option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          Area label
          <input name="zone" defaultValue="Demo Zone Kisumu" className={`${field} mt-1`} />
        </label>
        <label className="block text-sm">
          Check type
          <select name="screening_type" className={`${field} mt-1`} defaultValue="HPV_DNA">
            <option value="HPV_DNA">HPV DNA</option>
            <option value="VIA">Visual inspection</option>
            <option value="CYTOLOGY">Cytology</option>
          </select>
        </label>
        <label className="block text-sm">
          Finding
          <select name="result" className={`${field} mt-1`} defaultValue="positive">
            <option value="positive">Concerning — needs a closer look</option>
            <option value="suspected_cancer">Urgent — needs a closer look soon</option>
            <option value="negative">Not concerning — no case</option>
            <option value="inadequate">Inadequate sample — no case</option>
          </select>
        </label>
        <label className="flex items-start gap-2 text-sm">
          <input type="checkbox" name="sms" defaultChecked className="mt-1" />
          <span>They agree to discreet text reminders. Messages will not mention the check.</span>
        </label>
        <button className="rounded-full bg-lagoon px-4 py-2 text-sm text-white hover:bg-lagoon-deep">
          Save and open the case
        </button>
      </form>
    </main>
  );
}
