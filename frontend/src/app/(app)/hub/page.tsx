import { redirect } from "next/navigation";
import { HubSim } from "./HubSim";
import { Badge, Page, PageHeader } from "@/components/ui";
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
    <Page>
      <PageHeader
        title="Cuff hub"
        description="A synthetic demo of hub HUB-0007. The light always has a word beside it, and the server recomputes the label. Not a diagnostic device."
        meta={
          <>
            <Badge tone="outline">Synthetic</Badge>
            <Badge tone="warn">Pending clinical review</Badge>
          </>
        }
      />
      <HubSim booklets={booklets.map((item) => ({ ref: item.patient_ref, name: item.display_name }))} />
    </Page>
  );
}
