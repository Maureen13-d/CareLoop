import { redirect } from "next/navigation";
import { Notice } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { formatWhen } from "@/lib/format";
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
    <main className="space-y-6 px-4 py-6 md:px-0 md:py-0">
      <header>
        <p className="text-sm text-lagoon">Audit</p>
        <h1 className="mt-1 text-4xl">Who did what</h1>
        <p className="mt-2 max-w-xl text-ink-soft">
          State changes, sign-ins and handoffs. A person’s own words are not written here.
        </p>
      </header>
      {problem ? <Notice tone="bad">{problem}</Notice> : null}
      <div className="overflow-x-auto rounded-2xl border border-line bg-paper-2">
        <table className="w-full text-left text-sm">
          <thead className="text-ink-soft">
            <tr className="border-b border-line">
              <th className="px-4 py-3 font-medium">When (UTC)</th>
              <th className="px-4 py-3 font-medium">Who</th>
              <th className="px-4 py-3 font-medium">Action</th>
              <th className="px-4 py-3 font-medium">Outcome</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b border-line last:border-0">
                <td className="px-4 py-3 whitespace-nowrap">{formatWhen(row.occurred_at)}</td>
                <td className="px-4 py-3">{row.role ?? "system"}</td>
                <td className="px-4 py-3">
                  {row.action}
                  <span className="block text-ink-soft">
                    {row.entity_type}
                    {row.entity_id ? ` ${row.entity_id}` : ""}
                  </span>
                </td>
                <td className="px-4 py-3">{row.outcome}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
