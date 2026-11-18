import { Suspense } from "react";

type CaseView = {
  id: string;
  patient_ref: string;
  stage: string;
  stage_entered_at: string;
  overdue: boolean;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function getCases(): Promise<CaseView[] | null> {
  try {
    const res = await fetch(`${API}/cases`, { cache: "no-store" });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}

async function CasesTable() {
  const cases = await getCases();
  if (cases === null) {
    return (
      <p className="text-red-600">
        Could not reach the API at {API}. Is the backend running?
      </p>
    );
  }
  return (
    <table className="w-full text-left text-sm">
      <thead>
        <tr className="border-b">
          <th className="py-2">Case</th>
          <th>Patient</th>
          <th>Stage</th>
          <th>In stage since</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {cases.map((c) => (
          <tr key={c.id} className="border-b">
            <td className="py-2">{c.id}</td>
            <td>{c.patient_ref}</td>
            <td>{c.stage.replace("_", " ")}</td>
            <td>{new Date(c.stage_entered_at).toLocaleDateString()}</td>
            <td>
              {c.overdue ? (
                <span className="font-medium text-red-600">Overdue</span>
              ) : (
                <span className="text-green-700">On track</span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function Home() {
  return (
    <main className="mx-auto max-w-4xl p-8">
      <h1 className="text-2xl font-semibold">CareLoop</h1>
      <p className="mb-6 rounded bg-amber-100 p-2 text-sm text-amber-900">
        Synthetic data only. Not for clinical use.
      </p>
      <Suspense fallback={<p className="text-sm text-gray-500">Loading cases...</p>}>
        <CasesTable />
      </Suspense>
    </main>
  );
}
