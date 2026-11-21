import { ShieldCheck } from "lucide-react";
import { redirect } from "next/navigation";
import { Badge, EmptyState, Notice, Page, PageHeader, Table, Td, Th, THead, Tr, type Tone } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { ROLE_LABEL } from "@/lib/format";
import { sentence } from "@/lib/status";
import { getSession } from "@/lib/session";

export const instant = false;

type AuditRow = {
  id: number;
  occurred_at: string;
  role: string | null;
  action: string;
  entity_type: string;
  entity_id: number | null;
  outcome: string;
};

/** The first part of an action name ("case.transition" -> "case") is its category. */
function category(action: string): string {
  return action.split(/[._]/)[0] || action;
}

function outcomeTone(outcome: string): Tone {
  const text = outcome.toLowerCase();
  if (text.includes("denied") || text.includes("fail") || text.includes("error") || text.includes("refused")) return "danger";
  if (text.includes("success") || text === "ok") return "teal";
  return "neutral";
}

const day = (iso: string) => new Date(iso).toLocaleDateString("en-GB", { dateStyle: "medium", timeZone: "UTC" });
const time = (iso: string) => new Date(iso).toLocaleTimeString("en-GB", { timeStyle: "short", timeZone: "UTC" });

export default async function AuditPage() {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role !== "admin" && user.role !== "program_manager") redirect("/");

  let rows: AuditRow[] = [];
  let problem: string | null = null;
  try {
    rows = await api<AuditRow[]>("/audit?limit=40");
  } catch (error) {
    problem = error instanceof ApiError ? error.message : "The audit log could not be loaded.";
  }

  return (
    <Page>
      <PageHeader
        title="Who did what"
        description="State changes, sign-ins and handoffs, newest first. Times are UTC."
        meta={
          <Badge tone="teal" icon={<ShieldCheck aria-hidden="true" />}>
            A person’s own words are never written here
          </Badge>
        }
      />
      {problem ? <Notice tone="bad">{problem}</Notice> : null}
      {!problem && rows.length === 0 ? <EmptyState title="No events yet">Events appear as people use CareLoop.</EmptyState> : null}
      {rows.length > 0 ? (
        <>
          <Table caption="The 40 most recent audit events" className="hidden md:block">
            <THead>
              <Th>When</Th>
              <Th>Who</Th>
              <Th>Event</Th>
              <Th>Record</Th>
              <Th>Outcome</Th>
            </THead>
            <tbody>
              {rows.map((row) => (
                <Tr key={row.id}>
                  <Td className="whitespace-nowrap">
                    <time dateTime={row.occurred_at}>
                      <span className="block font-medium text-ink">{time(row.occurred_at)}</span>
                      <span className="text-ink-2">{day(row.occurred_at)}</span>
                    </time>
                  </Td>
                  <Td>{row.role ? (ROLE_LABEL[row.role] ?? sentence(row.role)) : <span className="text-ink-2">System</span>}</Td>
                  <Td>
                    <span className="flex flex-wrap items-center gap-2">
                      <Badge tone="outline">{sentence(category(row.action))}</Badge>
                      <span className="text-ink">{row.action}</span>
                    </span>
                  </Td>
                  <Td className="text-ink-2">
                    {sentence(row.entity_type)}
                    {row.entity_id ? ` ${row.entity_id}` : ""}
                  </Td>
                  <Td>
                    <Badge tone={outcomeTone(row.outcome)}>{sentence(row.outcome)}</Badge>
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>

          <ol className="space-y-2 md:hidden" aria-label="The 40 most recent audit events">
            {rows.map((row) => (
              <li key={row.id} className="rounded-2xl border border-line bg-surface p-4 shadow-raised">
                <div className="flex items-start justify-between gap-3">
                  <Badge tone="outline">{sentence(category(row.action))}</Badge>
                  <Badge tone={outcomeTone(row.outcome)}>{sentence(row.outcome)}</Badge>
                </div>
                <p className="mt-2 font-medium text-ink">{row.action}</p>
                <p className="mt-0.5 text-sm text-ink-2">
                  {row.role ? (ROLE_LABEL[row.role] ?? sentence(row.role)) : "System"}, {row.entity_type}
                  {row.entity_id ? ` ${row.entity_id}` : ""}
                </p>
                <p className="mt-1 text-[0.8125rem] text-ink-2">
                  <time dateTime={row.occurred_at}>
                    {day(row.occurred_at)}, {time(row.occurred_at)}
                  </time>
                </p>
              </li>
            ))}
          </ol>
        </>
      ) : null}
    </Page>
  );
}
