import { notFound, redirect } from "next/navigation";
import { moveBand, saveCheckin, saveReading } from "./actions";
import { Badge, Card, Field, Input, Notice, Page, PageHeader, SectionHeader, Select } from "@/components/ui";
import { SubmitButton } from "@/components/ui/submit-button";
import { ApiError, api } from "@/lib/api";
import { stageShort } from "@/lib/format";
import { riskTone } from "@/lib/status";
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

const SIGNS = [
  ["heavy_bleeding", "Heavy bleeding"],
  ["headache_severe", "Severe head pain"],
  ["vision_blurred", "Blurred vision"],
  ["swelling_face_hands", "Face or hand swelling"],
];

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
    <Page>
      <PageHeader
        back={{ href: "/", label: "Today" }}
        title={woman.display_name}
        description="You can record a check. You cannot move a clinical step. A colour is a label, not a diagnosis. Pending clinical review."
        meta={
          <>
            <Badge tone="outline">{woman.patient_ref}</Badge>
            <Badge tone="outline">{woman.area_label}</Badge>
            <Badge tone="outline">{woman.gestation_band}</Badge>
            <Badge tone="teal">{woman.case_state ? stageShort(woman.case_state) : "No journey"}</Badge>
            {woman.urgency === "urgent" ? <Badge tone="danger">Urgent</Badge> : null}
            <Badge tone={riskTone(woman.risk_level)}>{woman.risk_level ? `Label ${woman.risk_level}` : "No reading"}</Badge>
          </>
        }
      />
      {notice ? <Notice tone="ok">{notice}</Notice> : null}
      {error ? <Notice tone="bad">{error}</Notice> : null}

      <div className="grid items-start gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Card as="section" aria-labelledby="reading-heading">
            <SectionHeader id="reading-heading" title="Cuff reading" description="The server sets the label from the numbers and signs." />
            <form action={saveReading} className="mt-5 space-y-5">
              <input type="hidden" name="pregnancyId" value={woman.id} />
              <div className="grid grid-cols-3 gap-3">
                <Field label="Systolic" htmlFor="systolic">
                  <Input id="systolic" name="systolic" type="number" inputMode="numeric" defaultValue={118} />
                </Field>
                <Field label="Diastolic" htmlFor="diastolic">
                  <Input id="diastolic" name="diastolic" type="number" inputMode="numeric" defaultValue={76} />
                </Field>
                <Field label="Pulse" htmlFor="pulse">
                  <Input id="pulse" name="pulse" type="number" inputMode="numeric" defaultValue={72} />
                </Field>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Urine" htmlFor="urine_protein">
                  <Select id="urine_protein" name="urine_protein" defaultValue="neg">
                    {["neg", "trace", "1+", "2+", "3+", "unknown"].map((item) => (
                      <option key={item}>{item}</option>
                    ))}
                  </Select>
                </Field>
                <Field label="Haemoglobin" htmlFor="hb_band">
                  <Select id="hb_band" name="hb_band" defaultValue="normal">
                    {["normal", "mild", "moderate", "severe", "unknown"].map((item) => (
                      <option key={item}>{item}</option>
                    ))}
                  </Select>
                </Field>
              </div>
              <fieldset>
                <legend className="text-sm font-medium text-ink">Signs</legend>
                <div className="mt-2 grid gap-2 sm:grid-cols-2">
                  {SIGNS.map(([value, label]) => (
                    <label
                      key={value}
                      className="flex min-h-11 cursor-pointer items-center gap-3 rounded-xl border border-line px-3 text-sm has-[:checked]:border-danger/40 has-[:checked]:bg-danger-bg"
                    >
                      <input type="checkbox" name="sign" value={value} className="size-4 accent-deep" /> {label}
                    </label>
                  ))}
                </div>
              </fieldset>
              <SubmitButton pendingLabel="Saving">Save reading</SubmitButton>
            </form>
          </Card>

          <Card as="section" aria-labelledby="band-heading">
            <SectionHeader id="band-heading" title="Band" description="Lend, return or report a lost wrist band." />
            <form action={moveBand} className="mt-5 space-y-4">
              <input type="hidden" name="pregnancyId" value={woman.id} />
              <Field label="Device ID" htmlFor="device_id">
                <Input id="device_id" name="device_id" defaultValue="BAND-0012" />
              </Field>
              <div className="flex flex-wrap gap-2">
                {[
                  ["lend", "Lend"],
                  ["return", "Return"],
                  ["lost", "Report lost"],
                ].map(([action, label]) => (
                  <button
                    key={action}
                    type="submit"
                    name="action"
                    value={action}
                    className="inline-flex min-h-9 items-center rounded-full border border-line bg-surface px-4 text-sm font-medium text-ink hover:border-teal hover:bg-mint"
                  >
                    {label}
                  </button>
                ))}
              </div>
            </form>
          </Card>
        </div>

        <Card as="section" aria-labelledby="checkin-heading">
          <SectionHeader
            id="checkin-heading"
            title="Scripted check-in"
            description="Ask each question as written. Leave the first answer if nothing has changed."
          />
          <form action={saveCheckin} className="mt-5 space-y-5">
            <input type="hidden" name="pregnancyId" value={woman.id} />
            <Field label="Language" htmlFor="checkin-language">
              <Select id="checkin-language" name="language" defaultValue="en">
                <option value="en">English</option>
                <option value="sw">Swahili</option>
              </Select>
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Question name="bleeding" label="Bleeding" options={[["", "No"], ["yes", "Yes"]]} />
              <Question name="headache" label="Head pain" options={[["", "No"], ["mild", "Mild"], ["severe", "Severe"]]} />
              <Question name="vision" label="Vision" options={[["", "Clear"], ["blurred", "Blurred"]]} />
              <Question name="swelling" label="Swelling" options={[["", "No"], ["yes", "Face or hands"]]} />
              <Question name="pain" label="Belly pain" options={[["", "No"], ["upper", "High in the belly"]]} />
              <Question name="movement" label="Movement" options={[["", "Same"], ["less", "Less"], ["none", "None"]]} />
              <Question name="fever" label="Fever" options={[["", "No"], ["yes", "Yes"], ["severe", "With weakness"]]} />
              <Question name="fluid" label="Fluid" options={[["", "No"], ["yes", "Leaking"], ["fever", "Leaking and fever"]]} />
              <Question name="breathing" label="Breathing" options={[["", "Easy"], ["yes", "Hard"]]} />
              <Question name="mood" label="How she feels" options={[["", "Okay"], ["low", "Low"], ["unsafe", "Unsafe"]]} />
            </div>
            <SubmitButton pendingLabel="Saving">Save check-in</SubmitButton>
          </form>
        </Card>
      </div>
    </Page>
  );
}

function Question({ name, label, options }: { name: string; label: string; options: string[][] }) {
  return (
    <Field label={label} htmlFor={`checkin-${name}`}>
      <Select id={`checkin-${name}`} name={name} defaultValue="">
        {options.map(([value, text]) => (
          <option key={value || "none"} value={value}>
            {text}
          </option>
        ))}
      </Select>
    </Field>
  );
}
