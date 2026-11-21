import { FolderPlus } from "lucide-react";
import { redirect } from "next/navigation";
import { recordFinding } from "./actions";
import { Banner, Card, CheckField, Field, FormSection, Input, Notice, Page, PageHeader, Select } from "@/components/ui";
import { SubmitButton } from "@/components/ui/submit-button";
import { getSession } from "@/lib/session";

export const instant = false;

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
    <Page narrow>
      <PageHeader
        back={{ href: "/desk", label: "All cases" }}
        title="Open a case"
        description="Record a concerning check. This is not a diagnosis: with the person’s permission, it opens a navigation case so someone helps them reach a closer look."
      />
      <Banner>Nothing on this form is a real patient. Use a synthetic name and never type a real phone number.</Banner>
      {notice ? <Notice tone="ok">{notice}</Notice> : null}
      {error ? <Notice tone="bad" title="The finding was not saved">{error}</Notice> : null}

      <Card>
        <form action={recordFinding} className="space-y-8">
          <FormSection title="The person">
            <Field label="Synthetic name" htmlFor="display_name" hint="At least two characters. For example, Demo Amina.">
              <Input id="display_name" name="display_name" required minLength={2} placeholder="Demo Amina" aria-describedby="display_name-hint" />
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Age band" htmlFor="age_band">
                <Select id="age_band" name="age_band" defaultValue="30-34">
                  {["25-29", "30-34", "35-39", "40-44", "45-49", "50-54"].map((band) => (
                    <option key={band}>{band}</option>
                  ))}
                </Select>
              </Field>
              <Field label="Area label" htmlFor="zone">
                <Input id="zone" name="zone" defaultValue="Demo Zone Kisumu" />
              </Field>
            </div>
          </FormSection>

          <FormSection title="The check" description="Only a concerning or urgent finding opens a case.">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Check type" htmlFor="screening_type">
                <Select id="screening_type" name="screening_type" defaultValue="HPV_DNA">
                  <option value="HPV_DNA">HPV DNA</option>
                  <option value="VIA">Visual inspection</option>
                  <option value="CYTOLOGY">Cytology</option>
                </Select>
              </Field>
              <Field label="Finding" htmlFor="result">
                <Select id="result" name="result" defaultValue="positive">
                  <option value="positive">Concerning, needs a closer look</option>
                  <option value="suspected_cancer">Urgent, needs a closer look soon</option>
                  <option value="negative">Not concerning, no case</option>
                  <option value="inadequate">Inadequate sample, no case</option>
                </Select>
              </Field>
            </div>
          </FormSection>

          <FormSection
            title="Consent"
            description="Agreeing to be contacted about the next step is recorded with this case. Text reminders are a separate choice."
          >
            <CheckField
              name="sms"
              defaultChecked
              label="They agree to discreet text reminders"
              description="Messages give a time and a place only. They never mention the check, because phones are often shared."
            />
          </FormSection>

          <div className="flex flex-wrap items-center gap-3 border-t border-line pt-6">
            <SubmitButton pendingLabel="Opening the case">
              <FolderPlus aria-hidden="true" />
              Save and open the case
            </SubmitButton>
            <p className="text-sm text-ink-2">If a case opens, you go straight to it.</p>
          </div>
        </form>
      </Card>
    </Page>
  );
}
