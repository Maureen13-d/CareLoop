import { redirect } from "next/navigation";
import { Banner } from "@/components/ui";
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
    <main className="space-y-6 px-4 py-6 md:px-0 md:py-0">
      <header className="max-w-2xl">
        <p className="text-sm text-lagoon">Voice check-in · synthetic</p>
        <h1 className="mt-1 text-4xl">The same follow-up, spoken.</h1>
        <p className="mt-3 text-ink-soft">
          Pick a seeded person, hear the clinic check, and answer in words. Msingi speaks and
          listens. No phone call is placed.
        </p>
      </header>
      <Banner>
        These people are synthetic, with suggestive symptoms for the test. The guide does not
        diagnose. If they sound worse, it tells them to go to the nearest clinic.
      </Banner>
      {error ? <p className="text-sm text-clay">{error}</p> : <VoiceLab cases={cases} />}
    </main>
  );
}
