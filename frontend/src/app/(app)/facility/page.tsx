import { redirect } from "next/navigation";
import { api } from "@/lib/api";
import { getSession } from "@/lib/session";
import { markArrived, markLost } from "./actions";

export const instant = false;

type Summary = {
  synthetic: boolean;
  review: string;
  funnel: Record<string, number>;
  percent_arrived: number;
  median_hours_to_arrival: number | null;
  distribution_days: Record<string, number>;
  aging: { public_id: string; days: number; state: string }[];
  lost_queue: { public_id: string; case_id: number; state: string }[];
  note: string;
};

export default async function FacilityPage() {
  const user = await getSession();
  if (!user) redirect("/login");
  if (!["clinician", "navigator", "program_manager", "admin"].includes(user.role)) redirect("/");
  const data = await api<Summary>("/followup/facility");
  const percent = Math.round(data.percent_arrived * 100);

  return (
    <main className="space-y-6 px-4 py-6">
      <header>
        <p className="text-sm text-lagoon">SYNTHETIC · {data.review}</p>
        <h1 className="mt-1 text-4xl">Until they arrive</h1>
        <p className="mt-2 max-w-xl text-ink-soft">{data.note}</p>
      </header>
      <p className="text-2xl">{percent}% arrived</p>
      <p className="text-sm text-ink-soft">
        Median hours from screening to arrival:{" "}
        {data.median_hours_to_arrival == null ? "not enough arrivals yet" : data.median_hours_to_arrival.toFixed(1)}
      </p>
      <section>
        <h2 className="text-xl">Funnel</h2>
        <ul className="mt-2 space-y-1">
          {Object.entries(data.funnel).map(([state, count]) => (
            <li key={state} className="flex justify-between border-b border-line py-1">
              <span>{state}</span>
              <span>{count}</span>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2 className="text-xl">Days to arrival</h2>
        <ul className="mt-2 flex gap-3">
          {Object.entries(data.distribution_days).map(([bucket, count]) => (
            <li key={bucket} className="rounded-2xl border border-line px-3 py-2">
              {bucket}: {count}
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2 className="text-xl">Screened, not arrived</h2>
        <ul className="mt-2 space-y-2">
          {data.aging.map((row) => (
            <li key={row.public_id} className="rounded-2xl border border-line p-3">
              {row.public_id}: screened {row.days} days ago, not arrived ({row.state})
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2 className="text-xl">Lost to follow-up needs a person</h2>
        <ul className="mt-2 space-y-2">
          {data.lost_queue.map((row) => (
            <li key={row.case_id} className="flex flex-wrap items-center gap-2 rounded-2xl border border-line p-3">
              <span>{row.public_id}</span>
              <form action={markArrived}>
                <input type="hidden" name="case_id" value={row.case_id} />
                <button className="min-h-12 rounded-full bg-lagoon px-3 text-white" type="submit">
                  Record arrival
                </button>
              </form>
              <form action={markLost}>
                <input type="hidden" name="case_id" value={row.case_id} />
                <button className="min-h-12 rounded-full border border-line px-3" type="submit">
                  Close as lost
                </button>
              </form>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
