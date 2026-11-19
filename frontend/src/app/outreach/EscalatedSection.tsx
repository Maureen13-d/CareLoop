import Link from "next/link";
import { getEscalated } from "@/lib/outreach-api";

const fmtStage = (s: string) => s.replace(/_/g, " ");
const fmtTime = (iso: string) =>
  new Date(iso).toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  });

export async function EscalatedSection() {
  const escalated = await getEscalated();
  return (
    <section aria-labelledby="escalated-heading" className="space-y-3">
      <h2 id="escalated-heading" className="text-lg font-medium">
        Awaiting care coordinator
      </h2>
      {escalated.length === 0 ? (
        <p>No escalated cases.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">
              Cases where automated outreach is exhausted, most overdue first
            </caption>
            <thead>
              <tr className="border-b border-black/10 dark:border-white/15">
                <th scope="col" className="py-2 pr-4">Case</th>
                <th scope="col" className="pr-4">Patient</th>
                <th scope="col" className="pr-4">Stage</th>
                <th scope="col" className="pr-4">Days overdue</th>
                <th scope="col">Escalated (UTC)</th>
              </tr>
            </thead>
            <tbody>
              {escalated.map((e) => (
                <tr key={e.case_id} className="border-b border-black/10 dark:border-white/15">
                  <td className="py-2 pr-4">
                    <Link href={`/cases/${e.case_id}`} className="underline underline-offset-2">
                      {e.case_id}
                    </Link>
                  </td>
                  <td className="pr-4">{e.patient_ref}</td>
                  <td className="pr-4 capitalize">{fmtStage(e.stage)}</td>
                  <td className="pr-4">{e.days_overdue}</td>
                  <td>
                    <time dateTime={e.escalated_at}>{fmtTime(e.escalated_at)}</time>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
