import { redirect } from "next/navigation";
import { Badge, Banner, Page, PageHeader } from "@/components/ui";
import { getSession } from "@/lib/session";
import { loadVoiceCases } from "./actions";
import { VoiceLab } from "./VoiceLab";

export const instant = false;

export default async function VoicePage() {
  const user = await getSession();
  if (!user) redirect("/login");
  let cases: Awaited<ReturnType<typeof loadVoiceCases>> = [];
  let error = "";
  try {
    cases = await loadVoiceCases();
  } catch (caught) {
    error = caught instanceof Error ? caught.message : "The voice list could not be loaded.";
  }

  return (
    <Page>
      <PageHeader
        title="The same follow-up, spoken."
        description="Pick a seeded person, hear the clinic check, and answer in words. Msingi speaks and listens. No phone call is placed."
        meta={<Badge tone="outline">Synthetic voice check-in</Badge>}
      />
      <Banner>
        These people are synthetic, with suggestive symptoms for the test. The guide does not
        diagnose. If they sound worse, it tells them to go to the nearest clinic.
      </Banner>
      {error ? <p className="text-sm text-danger">{error}</p> : <VoiceLab cases={cases} />}
    </Page>
  );
}
