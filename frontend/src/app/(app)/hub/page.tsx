import { redirect } from "next/navigation";
import { HubSim } from "./HubSim";
import { api } from "@/lib/api";
import { getSession } from "@/lib/session";

export const instant = false;

const ALLOWED = new Set(["chw", "navigator", "clinician", "admin", "program_manager"]);

type Woman = { patient_ref: string; display_name: string };

export default async function HubPage() {
  const user = await getSession();
  if (!user) redirect("/login");
  if (!ALLOWED.has(user.role)) redirect("/");
  let booklets: Woman[] = [];
  try {
    booklets = await api<Woman[]>("/maternal/pregnancies");
  } catch {
    booklets = [];
  }
  return (
    <main className="space-y-6 px-4 py-6 md:px-0 md:py-0">
      <header className="max-w-2xl">
        <p className="text-sm text-lagoon">Hub simulator</p>
        <h1 className="mt-1 text-4xl">Cuff box</h1>
        <p className="mt-3 text-lg leading-relaxed text-ink-soft">
          Synthetic demo of hub HUB-0007. The light always has a word beside it. The server
          recomputes the label. PENDING CLINICAL REVIEW. Not a diagnostic device.
        </p>
      </header>
      <HubSim booklets={booklets.map((item) => ({ ref: item.patient_ref, name: item.display_name }))} />
    </main>
  );
}
