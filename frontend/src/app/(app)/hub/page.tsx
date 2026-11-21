import { redirect } from "next/navigation";
import { HubSim } from "./HubSim";
import { Badge, Page, PageHeader } from "@/components/ui";
import { getSession } from "@/lib/session";

export const instant = false;

export default async function HubPage() {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role !== "patient") redirect("/escalations");
  return (
    <Page>
      <PageHeader
        title="Cuff hub"
        description="The light always has a word beside it. A colour is a label, not a diagnosis. Booklets stay with the community health promoter, so this screen does not list anyone else."
        meta={
          <>
            <Badge tone="outline">Synthetic</Badge>
            <Badge tone="warn">Pending clinical review</Badge>
          </>
        }
      />
      <HubSim booklets={[]} />
    </Page>
  );
}
