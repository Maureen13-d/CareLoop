import { redirect } from "next/navigation";
import { ApiError, api } from "@/lib/api";
import { getSession } from "@/lib/session";

export const instant = false;

type ClipRow = {
  id: number;
  template_id: string;
  label: string;
  status: string;
  pilot_enabled: boolean;
};

export default async function KslReviewPage() {
  const user = await getSession();
  if (!user) redirect("/login");
  const allowed = ["admin", "program_manager", "ksl_reviewer", "navigator", "clinician"];
  if (!allowed.includes(user.role)) redirect("/");

  let rows: ClipRow[] = [];
  let problem: string | null = null;
  try {
    rows = await api<ClipRow[]>("/ksl/clips");
  } catch (error) {
    problem = error instanceof ApiError ? error.message : "The clip list could not be loaded.";
  }

  return (
    <main className="space-y-6 px-4 py-6 md:px-0 md:py-0">
      <header>
        <p className="text-sm text-lagoon">KSL clips</p>
        <h1 className="mt-1 text-4xl">Clip review</h1>
        <p className="mt-2 max-w-xl text-ink-soft">
          A clip can be approved only after two Deaf passes and a different confirmer. Pending
          clinical lines stay off for a pilot. This list stores labels, not a person’s footage.
        </p>
      </header>
      {problem ? <p className="text-lg">{problem}</p> : null}
      {rows.length === 0 && !problem ? <p className="text-lg">No clips have been uploaded.</p> : null}
      <ul className="space-y-3">
        {rows.map((row) => (
          <li key={row.id} className="rounded-2xl border border-line bg-white p-4">
            <p className="text-lg">{row.template_id}</p>
            <p className="text-sm">
              {row.status} · {row.label}
              {row.pilot_enabled ? " · pilot" : " · not for a pilot"}
            </p>
          </li>
        ))}
      </ul>
    </main>
  );
}
