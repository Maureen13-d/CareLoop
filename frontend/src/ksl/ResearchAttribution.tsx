import { RESEARCH_CITATION, RESEARCH_LABEL } from "./researchLabel.js";

export function ResearchAttribution() {
  return (
    <footer className="space-y-2 rounded-xl border border-line bg-surface px-4 py-3 text-sm text-ink-2">
      <p className="font-semibold text-ink">{RESEARCH_LABEL}</p>
      <p>{RESEARCH_CITATION}</p>
    </footer>
  );
}
