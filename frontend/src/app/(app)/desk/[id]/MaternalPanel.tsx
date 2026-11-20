import { coverCheck, noteBarrier, voucherStep } from "./maternal-actions";
import { ApiError, api } from "@/lib/api";

type Reading = {
  id: number;
  taken_at: string;
  systolic: number | null;
  diastolic: number | null;
  risk_level: string;
  source: string;
  danger_signs: string[];
};

type Bundle = {
  readings: Reading[];
  band: { device_id: string; status: string; battery_pct: number | null } | null;
  barriers: string[];
  vouchers: { id: number; status: string; amount_label: string; provider: string }[];
  cover_checks: { id: number; status: string; source: string }[];
  review: string;
  gestation_band: string;
  area_label: string;
};

const BARRIERS = [
  ["fare", "Fare"],
  ["cover", "Cover"],
  ["fear", "Fear"],
  ["companion", "Companion"],
  ["shared_phone", "Shared phone"],
];

export async function MaternalPanel({ caseId }: { caseId: number }) {
  let bundle: Bundle;
  try {
    bundle = await api<Bundle>(`/maternal/cases/${caseId}`);
  } catch (error) {
    const message = error instanceof ApiError ? error.message : "The maternal record could not load.";
    return <p className="text-sm text-danger">{message}</p>;
  }
  const voucher = bundle.vouchers.at(-1);
  const cover = bundle.cover_checks.at(-1);
  return (
    <section aria-labelledby="maternal-heading" className="space-y-4">
      <h2 id="maternal-heading" className="text-2xl">Maternal record</h2>
      <p className="text-sm text-ink-soft">
        {bundle.area_label} · {bundle.gestation_band}. {bundle.review}. A colour is a label, not a diagnosis.
      </p>
      <ReadingChart readings={bundle.readings} />
      <ul className="space-y-2">
        {bundle.readings.length === 0 ? <li className="text-sm">No cuff reading yet.</li> : null}
        {bundle.readings.map((row) => (
          <li key={row.id} className="rounded-2xl border border-line bg-white px-4 py-3 text-sm">
            {row.taken_at} · {row.systolic ?? "—"}/{row.diastolic ?? "—"} · label {row.risk_level} · {row.source}
            {row.danger_signs.length ? ` · ${row.danger_signs.join(", ")}` : ""}
          </li>
        ))}
      </ul>
      <p className="text-sm">
        Band: {bundle.band ? `${bundle.band.device_id} · ${bundle.band.status} · battery ${bundle.band.battery_pct ?? "unknown"}%` : "none lent"}
      </p>
      <p className="text-sm">Barriers: {bundle.barriers.length ? bundle.barriers.join(", ") : "none noted"}</p>
      <div className="flex flex-wrap gap-2">
        {BARRIERS.map(([flag, label]) => (
          <form key={flag} action={noteBarrier}>
            <input type="hidden" name="caseId" value={caseId} />
            <input type="hidden" name="flag" value={flag} />
            <button className="min-h-12 rounded-full border border-line bg-white px-4 text-sm">{label}</button>
          </form>
        ))}
      </div>
      <p className="text-sm">
        Voucher: {voucher ? `${voucher.status} · ${voucher.amount_label} · ${voucher.provider}` : "none"}
      </p>
      <div className="flex flex-wrap gap-2">
        {["request", "approve", "issue", "used"].map((action) => (
          <form key={action} action={voucherStep}>
            <input type="hidden" name="caseId" value={caseId} />
            <input type="hidden" name="action" value={action} />
            <button className="min-h-12 rounded-full border border-line bg-white px-4 text-sm">{action}</button>
          </form>
        ))}
      </div>
      <p className="text-sm">Cover: {cover ? `${cover.status} · ${cover.source}` : "not checked"}</p>
      <form action={coverCheck} className="flex flex-wrap items-center gap-2">
        <input type="hidden" name="caseId" value={caseId} />
        <select name="status" className="min-h-12 rounded-xl border border-line bg-white px-3 text-sm">
          <option value="unknown">unknown</option>
          <option value="assumed_covered">assumed covered</option>
          <option value="assumed_not_covered">assumed not covered</option>
        </select>
        <button className="min-h-12 rounded-full bg-lagoon px-4 text-sm text-white">Record simulated cover</button>
      </form>
    </section>
  );
}

function ReadingChart({ readings }: { readings: Reading[] }) {
  const points = readings.filter((row) => row.systolic != null);
  if (points.length === 0) return null;
  const width = 280;
  const height = 72;
  const values = points.map((row) => row.systolic as number);
  const max = Math.max(180, ...values);
  const min = Math.min(70, ...values);
  const coords = points.map((row, index) => {
    const x = points.length === 1 ? width / 2 : (index / (points.length - 1)) * width;
    const y = height - ((row.systolic as number) - min) / (max - min || 1) * height;
    return `${x},${y}`;
  });
  return (
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Systolic readings over time" className="h-20 w-full text-lagoon">
      <polyline fill="none" stroke="currentColor" strokeWidth="3" points={coords.join(" ")} />
    </svg>
  );
}
