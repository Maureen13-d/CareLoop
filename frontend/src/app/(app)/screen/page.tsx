import { IdCard } from "lucide-react";
import { redirect } from "next/navigation";
import { Badge, Banner, Card, CheckField, Field, FormSection, Input, Notice, Page, PageHeader, Select } from "@/components/ui";
import { SubmitButton } from "@/components/ui/submit-button";
import { getSession } from "@/lib/session";
import { registerScreening } from "./actions";

export const instant = false;

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
    <Page narrow>
      <PageHeader
        title="Issue an ID card"
        description="Record a screening. A concerning or urgent finding, with consent, opens follow-up and issues a random ID. The contact is stored apart from the card and never printed on it."
        meta={
          <>
            <Badge tone="outline">Synthetic</Badge>
            <Badge tone="warn">Pending clinical review</Badge>
          </>
        }
      />
      <Banner>Synthetic demo only. Do not type a real phone number.</Banner>
      {notice ? <Notice tone="ok" title="Saved">Status: {notice}</Notice> : null}
      {error ? <Notice tone="bad" title="The screening was not saved">{error}</Notice> : null}

      <Card>
        <form action={registerScreening} className="space-y-8">
          <FormSection title="The person">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Age band" htmlFor="age_band">
                <Select id="age_band" name="age_band" defaultValue="30-34">
                  <option>20-24</option>
                  <option>25-29</option>
                  <option>30-34</option>
                  <option>35-39</option>
                  <option>40-44</option>
                </Select>
              </Field>
              <Field label="Area label" htmlFor="area_label">
                <Input id="area_label" name="area_label" required defaultValue="Demo Zone A" />
              </Field>
            </div>
          </FormSection>

          <FormSection title="The screening">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Screening type" htmlFor="screening_type">
                <Select id="screening_type" name="screening_type" defaultValue="general">
                  <option value="general">General</option>
                  <option value="cervical">Cervical</option>
                  <option value="blood_pressure">Blood pressure</option>
                  <option value="hiv">HIV</option>
                  <option value="tb">TB</option>
                </Select>
              </Field>
              <Field label="Finding" htmlFor="finding" hint="Only concerning or urgent opens follow-up.">
                <Select id="finding" name="finding" defaultValue="concerning" aria-describedby="finding-hint">
                  <option value="concerning">Concerning</option>
                  <option value="urgent">Urgent</option>
                  <option value="not_concerning">Not concerning</option>
                  <option value="inadequate">Inadequate</option>
                </Select>
              </Field>
            </div>
          </FormSection>

          <FormSection title="How to reach them">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Language" htmlFor="language">
                <Select id="language" name="language" defaultValue="en">
                  <option value="en">English</option>
                  <option value="sw">Kiswahili</option>
                </Select>
              </Field>
              <Field label="Preferred channel" htmlFor="channel">
                <Select id="channel" name="channel" defaultValue="telegram">
                  <option value="telegram">Telegram</option>
                  <option value="sms">SMS</option>
                  <option value="ussd">USSD</option>
                  <option value="web">Web</option>
                  <option value="voice">Voice</option>
                </Select>
              </Field>
            </div>
            <Field label="Contact" htmlFor="contact" hint="Kept in a separate store. It is not printed on the card.">
              <Input id="contact" name="contact" placeholder="07…" inputMode="tel" aria-describedby="contact-hint" />
            </Field>
            <CheckField
              name="consent"
              defaultChecked
              label="Consent to follow-up"
              description="Without consent no ID is issued and no follow-up is opened."
            />
          </FormSection>

          <div className="flex flex-wrap items-center gap-3 border-t border-line pt-6">
            <SubmitButton pendingLabel="Issuing">
              <IdCard aria-hidden="true" />
              Issue ID
            </SubmitButton>
            <p className="text-sm text-ink-2">If an ID is issued, its printable card opens next.</p>
          </div>
        </form>
      </Card>
    </Page>
  );
}
