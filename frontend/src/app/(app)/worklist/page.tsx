import { redirect } from "next/navigation";
import { api } from "@/lib/api";
import { getSession } from "@/lib/session";
import { claimCase, escalateCase, logAttempt, recordOutcome } from "./actions";

export const instant = false;

type Row = {
  case_id: number;
  public_id: string;
  days_since_screening: number;
  state: string;
  reason: string;
  recommended_action: string;
};

type Worklist = {
  synthetic: boolean;
  review: string;
  counts: { open: number; overdue: number; worse: number; unreached: number };
  rows: Row[];
};

const button = "min-h-12 rounded-full border border-line px-3 text-sm";

export default async function WorklistPage() {
  const user = await getSession();
  if (!user) redirect("/login");
  if (!["chw", "navigator", "clinician", "admin", "program_manager"].includes(user.role)) {
    redirect("/");
  }
  const data = await api<Worklist>("/followup/worklist");

  return (
    <main className="space-y-6 px-4 py-6">
      <header>
        <p className="text-sm text-lagoon">SYNTHETIC · {data.review}</p>
        <h1 className="mt-1 text-4xl">Who to chase</h1>
        <p className="mt-2 text-ink-soft">
          Ranked by urgency. A worsening report is always first. A late visit is a problem to
          solve, not the person’s fault.
        </p>
      </header>
      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {(
          [
            ["Open", data.counts.open],
            ["Overdue", data.counts.overdue],
            ["Worse", data.counts.worse],
            ["Unreached", data.counts.unreached],
          ] as const
        ).map(([label, value]) => (
          <div key={label} className="rounded-2xl border border-line bg-paper-2 p-3">
            <dt className="text-sm text-ink-soft">{label}</dt>
            <dd className="text-3xl">{value}</dd>
          </div>
        ))}
      </dl>
      <ul className="space-y-3">
        {data.rows.map((row) => (
          <li key={row.public_id} className="rounded-2xl border border-line bg-white p-4">
            <p className="text-lg tracking-wide">{row.public_id}</p>
            <p className="text-sm text-ink-soft">
              {row.days_since_screening} days · {row.state}
            </p>
            <p className="mt-2">{row.reason}</p>
            <p className="mt-1 text-sm">Next: {row.recommended_action}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <form action={claimCase}>
                <input type="hidden" name="case_id" value={row.case_id} />
                <button className={button} type="submit">
                  Claim
                </button>
              </form>
              <form action={logAttempt}>
                <input type="hidden" name="case_id" value={row.case_id} />
                <button className={button} type="submit">
                  Log attempt
                </button>
              </form>
              <form action={escalateCase}>
                <input type="hidden" name="case_id" value={row.case_id} />
                <button className={button} type="submit">
                  Escalate
                </button>
              </form>
              <form action={recordOutcome} className="flex gap-2">
                <input type="hidden" name="case_id" value={row.case_id} />
                <select name="label" className="min-h-12 rounded-full border border-line px-2 text-sm">
                  <option value="reached">Reached</option>
                  <option value="not_home">Not home</option>
                  <option value="barrier_noted">Barrier noted</option>
                </select>
                <button className={button} type="submit">
                  Save
                </button>
              </form>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
