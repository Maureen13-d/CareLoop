export function Banner({ children }: { children: React.ReactNode }) {
  return (
    <p
      role="note"
      className="rounded-2xl border border-gold/40 bg-[#f8efd4] px-4 py-3 text-sm leading-relaxed text-ink"
    >
      {children}
    </p>
  );
}

export function Stat({ label, value, hint }: { label: string; value: number; hint?: string }) {
  return (
    <div className="rounded-2xl border border-line bg-paper-2 px-4 py-4">
      <p className="text-sm text-ink-soft">{label}</p>
      <p className="mt-1 font-serif text-3xl text-ink">{value}</p>
      {hint ? <p className="mt-1 text-xs text-ink-soft">{hint}</p> : null}
    </div>
  );
}

export function Notice({ tone, children }: { tone: "ok" | "bad"; children: React.ReactNode }) {
  const styles =
    tone === "ok"
      ? "border-moss/30 bg-[#e7f2e6] text-moss"
      : "border-danger/30 bg-[#f8e8e4] text-danger";
  return (
    <p role="status" className={`rounded-2xl border px-4 py-3 text-sm ${styles}`}>
      {children}
    </p>
  );
}
