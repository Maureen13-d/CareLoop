import { redirect } from "next/navigation";
import { HubSim } from "./HubSim";
import { Badge, Page, PageHeader } from "@/components/ui";
import { api } from "@/lib/api";
import { getSession } from "@/lib/session";

export const instant = false;

export default async function HubPage() {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role !== "patient") redirect("/escalations");
  // Only the signed-in patient's own booklet. A yellow or red reading then reaches a navigator.
  let ref: string | null = null;
  try {
    ref = (await api<{ ref: string | null }>("/followup/my-booklet")).ref;
  } catch {
    ref = null;
  }
  return (
    <Page>
      <PageHeader
        title="Cuff hub"
        description="The light always has a word beside it. A colour is a label, not a diagnosis. Readings go to your own booklet: yellow lets a navigator know, red goes to them as urgent."
        meta={
          <>
            <Badge tone="outline">Synthetic</Badge>
            <Badge tone="warn">Pending clinical review</Badge>
          </>
        }
      />
      <HubSim booklets={ref ? [{ ref, name: "Your booklet" }] : []} />
    </Page>
  );
}
