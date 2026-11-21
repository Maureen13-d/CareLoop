import { coverCheck, noteBarrier, voucherStep } from "./maternal-actions";
import { Badge, Notice, SectionHeader, Select } from "@/components/ui";
import { SubmitButton } from "@/components/ui/submit-button";
import { ApiError, api } from "@/lib/api";
import { riskTone, sentence } from "@/lib/status";

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

const VOUCHER_STEPS = [
  ["request", "Request"],
  ["approve", "Approve"],
  ["issue", "Issue"],
  ["used", "Mark used"],
];

function Row({ label, value, children }: { label: string; value: React.ReactNode; children?: React.ReactNode }) {
  return (
    <div className="grid gap-3 border-t border-line py-4 sm:grid-cols-[9rem_1fr]">
      <p className="text-sm font-medium text-ink">{label}</p>
      <div className="space-y-3">
        <div className="text-sm text-ink-2">{value}</div>
        {children}
      </div>
    </div>
  );
}

export async function MaternalPanel({ caseId }: { caseId: number }) {
  let bundle: Bundle;
  try {
    bundle = await api<Bundle>(`/maternal/cases/${caseId}`);
  } catch (error) {
    const message = error instanceof ApiError ? error.message : "The maternal record could not load.";
    return <Notice tone="bad">{message}</Notice>;
  }
  const voucher = bundle.vouchers.at(-1);
  const cover = bundle.cover_checks.at(-1);
  return (
    <section aria-labelledby="maternal-heading">
      <SectionHeader
        id="maternal-heading"
        title="Maternal record"
        description={`${bundle.area_label}, ${bundle.gestation_band}. ${sentence(bundle.review.toLowerCase())}. A colour is a label, not a diagnosis.`}
      />

      <div className="mt-5">
        <p className="text-sm font-medium text-ink">Cuff readings</p>
        {bundle.readings.length === 0 ? (
          <p className="mt-1 text-sm text-ink-2">No cuff reading yet.</p>
        ) : (
          <>
            <ReadingChart readings={bundle.readings} />
            <ul className="mt-2 divide-y divide-line overflow-hidden rounded-xl border border-line">
              {bundle.readings.map((row) => (
                <li key={row.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-2.5 text-sm">
                  <span className="text-ink-2">{row.taken_at}</span>
                  <span className="font-medium tabular-nums text-ink">
                    {row.systolic ?? "–"}/{row.diastolic ?? "–"}
                  </span>
                  <Badge tone={riskTone(row.risk_level)}>Label {row.risk_level}</Badge>
                  <span className="text-ink-2">{sentence(row.source)}</span>
                  {row.danger_signs.length ? (
                    <span className="w-full text-danger sm:w-auto">{row.danger_signs.map(sentence).join(", ")}</span>
                  ) : null}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>

      <div className="mt-5">
        <Row
          label="Band"
          value={
            bundle.band
              ? `${bundle.band.device_id}, ${bundle.band.status}, battery ${bundle.band.battery_pct ?? "unknown"}%`
              : "None lent"
          }
        />
        <Row label="Barriers" value={bundle.barriers.length ? bundle.barriers.map(sentence).join(", ") : "None noted"}>
          <div className="flex flex-wrap gap-2">
            {BARRIERS.map(([flag, label]) => (
              <form key={flag} action={noteBarrier}>
                <input type="hidden" name="caseId" value={caseId} />
                <input type="hidden" name="flag" value={flag} />
                <SubmitButton variant="secondary" size="sm">
                  {label}
                </SubmitButton>
              </form>
            ))}
          </div>
        </Row>
        <Row
          label="Transport voucher"
          value={voucher ? `${sentence(voucher.status)}, ${voucher.amount_label}, ${voucher.provider}` : "None"}
        >
          <div className="flex flex-wrap gap-2">
            {VOUCHER_STEPS.map(([action, label]) => (
              <form key={action} action={voucherStep}>
                <input type="hidden" name="caseId" value={caseId} />
                <input type="hidden" name="action" value={action} />
                <SubmitButton variant="secondary" size="sm">
                  {label}
                </SubmitButton>
              </form>
            ))}
          </div>
        </Row>
        <Row label="Cover" value={cover ? `${sentence(cover.status)}, ${cover.source}` : "Not checked"}>
          <form action={coverCheck} className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <input type="hidden" name="caseId" value={caseId} />
            <label htmlFor="cover-status" className="sr-only">
              Simulated cover status
            </label>
            <Select id="cover-status" name="status" className="sm:max-w-56">
              <option value="unknown">Unknown</option>
              <option value="assumed_covered">Assumed covered</option>
              <option value="assumed_not_covered">Assumed not covered</option>
            </Select>
            <SubmitButton size="sm">Record simulated cover</SubmitButton>
          </form>
        </Row>
      </div>
    </section>
  );
}

function ReadingChart({ readings }: { readings: Reading[] }) {
  const points = readings.filter((row) => row.systolic != null);
  if (points.length === 0) return null;
  const width = 320;
  const height = 80;
  const values = points.map((row) => row.systolic as number);
  const max = Math.max(180, ...values);
  const min = Math.min(70, ...values);
  const coords = points.map((row, index) => {
    const x = points.length === 1 ? width / 2 : 8 + (index / (points.length - 1)) * (width - 16);
    const y = 8 + (height - 16) - (((row.systolic as number) - min) / (max - min || 1)) * (height - 16);
    return { x, y, level: row.risk_level };
  });
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={`Systolic readings over time: ${values.join(", ")}`}
      className="mt-2 h-auto w-full max-w-xl rounded-xl bg-canvas"
    >
      <polyline
        fill="none"
        stroke="var(--teal)"
        strokeWidth="2.5"
        strokeLinejoin="round"
        points={coords.map((point) => `${point.x},${point.y}`).join(" ")}
      />
      {coords.map((point, index) => (
        <circle
          key={index}
          cx={point.x}
          cy={point.y}
          r="3.5"
          fill={point.level === "red" ? "var(--danger)" : point.level === "yellow" ? "var(--warn)" : "var(--deep)"}
        />
      ))}
    </svg>
  );
}
