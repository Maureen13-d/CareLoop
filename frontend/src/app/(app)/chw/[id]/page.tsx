import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { moveBand, saveCheckin, saveReading } from "./actions";
import { Notice } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { stageShort } from "@/lib/format";
import { getSession } from "@/lib/session";

export const instant = false;

type Woman = {
  id: number;
  patient_ref: string;
  display_name: string;
  gestation_band: string;
  area_label: string;
  case_id: number | null;
  case_state: string | null;
  urgency: string | null;
  risk_level: string | null;
};

const field = "min-h-12 w-full rounded-xl border border-line bg-white px-3";

export default async function ChwWomanPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ notice?: string; error?: string }>;
}) {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role !== "chw" && user.role !== "navigator") redirect("/");
  const { id } = await params;
  const { notice, error } = await searchParams;
  if (!/^\d+$/.test(id)) notFound();
  let women: Woman[] = [];
  try {
    women = await api<Woman[]>("/maternal/pregnancies");
  } catch (err) {
    if (err instanceof ApiError && err.status === 403) redirect("/");
    throw err;
  }
  const woman = women.find((item) => item.id === Number(id));
  if (!woman) notFound();

  return (
    <main className="space-y-8 px-4 py-6 md:px-0 md:py-0">
      <Link href="/" className="text-sm text-lagoon underline underline-offset-2">Today</Link>
      {notice ? <Notice tone="ok">{notice}</Notice> : null}
      {error ? <Notice tone="bad">{error}</Notice> : null}
      <header>
        <p className="text-sm text-lagoon">{woman.patient_ref}</p>
        <h1 className="text-4xl">{woman.display_name}</h1>
        <p className="mt-2 text-ink-soft">
          {woman.area_label} · {woman.gestation_band} · {woman.case_state ? stageShort(woman.case_state) : "No journey"}
          {woman.urgency === "urgent" ? " · Urgent" : ""} · {woman.risk_level ? `label ${woman.risk_level}` : "no reading"}
        </p>
        <p className="mt-2 max-w-2xl text-sm text-ink-soft">
          You can record a check. You cannot move a clinical step. A colour is a label, not a diagnosis. PENDING CLINICAL REVIEW.
        </p>
      </header>

      <form action={saveReading} className="space-y-3 rounded-2xl border border-line bg-paper-2 p-4">
        <h2 className="text-2xl">Cuff reading</h2>
        <input type="hidden" name="pregnancyId" value={woman.id} />
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="text-sm">Systolic<input className={field} name="systolic" type="number" defaultValue={118} /></label>
          <label className="text-sm">Diastolic<input className={field} name="diastolic" type="number" defaultValue={76} /></label>
          <label className="text-sm">Pulse<input className={field} name="pulse" type="number" defaultValue={72} /></label>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm">Urine<select className={field} name="urine_protein" defaultValue="neg">{["neg", "trace", "1+", "2+", "3+", "unknown"].map((item) => <option key={item}>{item}</option>)}</select></label>
          <label className="text-sm">Haemoglobin<select className={field} name="hb_band" defaultValue="normal">{["normal", "mild", "moderate", "severe", "unknown"].map((item) => <option key={item}>{item}</option>)}</select></label>
        </div>
        <fieldset className="grid gap-2 sm:grid-cols-2">
          <legend className="text-sm">Signs</legend>
          {[
            ["heavy_bleeding", "Heavy bleeding"],
            ["headache_severe", "Severe head pain"],
            ["vision_blurred", "Blurred vision"],
            ["swelling_face_hands", "Face or hand swelling"],
          ].map(([value, label]) => (
            <label key={value} className="flex min-h-12 items-center gap-2 text-sm">
              <input type="checkbox" name="sign" value={value} /> {label}
            </label>
          ))}
        </fieldset>
        <button className="min-h-12 rounded-full bg-lagoon px-4 text-white">Save reading</button>
      </form>

      <form action={saveCheckin} className="space-y-3 rounded-2xl border border-line bg-paper-2 p-4">
        <h2 className="text-2xl">Scripted check-in</h2>
        <input type="hidden" name="pregnancyId" value={woman.id} />
        <label className="block text-sm">Language
          <select className={field} name="language" defaultValue="en">
            <option value="en">English</option>
            <option value="sw">Swahili</option>
          </select>
        </label>
        <Select name="bleeding" label="Bleeding" options={[["", "No"], ["yes", "Yes"]]} />
        <Select name="headache" label="Head pain" options={[["", "No"], ["mild", "Mild"], ["severe", "Severe"]]} />
        <Select name="vision" label="Vision" options={[["", "Clear"], ["blurred", "Blurred"]]} />
        <Select name="swelling" label="Swelling" options={[["", "No"], ["yes", "Face or hands"]]} />
        <Select name="pain" label="Belly pain" options={[["", "No"], ["upper", "High in the belly"]]} />
        <Select name="movement" label="Movement" options={[["", "Same"], ["less", "Less"], ["none", "None"]]} />
        <Select name="fever" label="Fever" options={[["", "No"], ["yes", "Yes"], ["severe", "With weakness"]]} />
        <Select name="fluid" label="Fluid" options={[["", "No"], ["yes", "Leaking"], ["fever", "Leaking and fever"]]} />
        <Select name="breathing" label="Breathing" options={[["", "Easy"], ["yes", "Hard"]]} />
        <Select name="mood" label="How she feels" options={[["", "Okay"], ["low", "Low"], ["unsafe", "Unsafe"]]} />
        <button className="min-h-12 rounded-full bg-lagoon px-4 text-white">Save check-in</button>
      </form>

      <form action={moveBand} className="space-y-3 rounded-2xl border border-line bg-paper-2 p-4">
        <h2 className="text-2xl">Band</h2>
        <input type="hidden" name="pregnancyId" value={woman.id} />
        <label className="block text-sm">Device id
          <input className={field} name="device_id" defaultValue="BAND-0012" />
        </label>
        <div className="flex flex-wrap gap-2">
          {["lend", "return", "lost"].map((action) => (
            <button key={action} name="action" value={action} className="min-h-12 rounded-full border border-line bg-white px-4 text-sm">
              {action}
            </button>
          ))}
        </div>
      </form>
    </main>
  );
}

function Select({ name, label, options }: { name: string; label: string; options: string[][] }) {
  return (
    <label className="block text-sm">
      {label}
      <select className={field} name={name} defaultValue="">
        {options.map(([value, text]) => (
          <option key={value || "none"} value={value}>{text}</option>
        ))}
      </select>
    </label>
  );
}
