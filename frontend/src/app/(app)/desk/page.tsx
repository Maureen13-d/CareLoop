import Link from "next/link";
import { redirect } from "next/navigation";
import { Notice } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { stageShort } from "@/lib/format";
import { getSession } from "@/lib/session";

export const instant = false;

type CaseRow = {
  id: number;
  patient_ref: string | null;
  patient_display_name: string | null;
  state: string;
  state_label: string;
  urgency: string;
  owner_user_name: string | null;
  unowned: boolean;
  overdue: boolean;
  hours_overdue: number | null;
  open_escalations: number;
};

const FILTERS = [
  { id: "open", label: "Open" },
  { id: "overdue", label: "Past deadline" },
  { id: "unowned", label: "No owner" },
  { id: "all", label: "Everything" },
] as const;

function queryFor(filter: string): string {
  if (filter === "overdue") return "/cases?status=open&overdue=true&limit=100";
  if (filter === "unowned") return "/cases?status=open&unowned=true&limit=100";
  if (filter === "all") return "/cases?status=all&limit=100";
  return "/cases?status=open&limit=100";
}

export default async function DeskPage({
  searchParams,
}: {
  searchParams: Promise<{ filter?: string }>;
}) {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role !== "navigator" && user.role !== "clinician") redirect("/");
  const { filter = "open" } = await searchParams;
  const active = FILTERS.some((item) => item.id === filter) ? filter : "open";

  let cases: CaseRow[] = [];
  let problem: string | null = null;
  try {
    cases = await api<CaseRow[]>(queryFor(active));
  } catch (error) {
    problem = error instanceof ApiError ? error.message : "Cases could not be loaded.";
  }

  return (
    <main className="space-y-6 px-4 py-6 md:px-0 md:py-0">
      <header>
        <p className="text-sm text-lagoon">Cases</p>
        <h1 className="mt-1 text-4xl">Everyone on the pathway</h1>
        <p className="mt-2 max-w-xl text-ink-soft">
          A case opens when a clinician records a concerning finding and the person has agreed
          to be contacted. Names here are synthetic.
        </p>
      </header>
      <div className="flex flex-wrap gap-2" role="tablist" aria-label="Filter cases">
        {FILTERS.map((item) => (
          <Link
            key={item.id}
            href={item.id === "open" ? "/desk" : `/desk?filter=${item.id}`}
            className={`rounded-full px-3 py-1.5 text-sm ${
              active === item.id ? "bg-ink text-white" : "border border-line bg-paper-2"
            }`}
            aria-current={active === item.id ? "page" : undefined}
          >
            {item.label}
          </Link>
        ))}
      </div>
      {problem ? <Notice tone="bad">{problem}</Notice> : null}
      {cases.length === 0 && !problem ? (
        <p>No cases in this view.</p>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-line bg-paper-2">
          <table className="w-full text-left text-sm">
            <thead className="text-ink-soft">
              <tr className="border-b border-line">
                <th className="px-4 py-3 font-medium">Person</th>
                <th className="px-4 py-3 font-medium">Where</th>
                <th className="px-4 py-3 font-medium">Owner</th>
                <th className="px-4 py-3 font-medium">Attention</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((item) => (
                <tr key={item.id} className="border-b border-line last:border-0">
                  <td className="px-4 py-3">
                    <Link href={`/desk/${item.id}`} className="font-medium underline decoration-line underline-offset-2">
                      {item.patient_display_name}
                    </Link>
                    <span className="mt-0.5 block text-ink-soft">{item.patient_ref}</span>
                  </td>
                  <td className="px-4 py-3">
                    {stageShort(item.state)}
                    {item.urgency === "urgent" ? (
                      <span className="ml-2 rounded-full bg-[#f8e8e4] px-2 py-0.5 text-xs text-danger">Urgent</span>
                    ) : null}
                  </td>
                  <td className="px-4 py-3">{item.owner_user_name ?? "Unowned"}</td>
                  <td className="px-4 py-3 text-clay">
                    {item.overdue
                      ? `${item.hours_overdue}h past deadline`
                      : item.open_escalations
                        ? "Escalated"
                        : "On time"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
