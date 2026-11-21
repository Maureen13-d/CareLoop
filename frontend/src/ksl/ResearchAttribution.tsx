import { RESEARCH_CITATION, RESEARCH_LABEL } from "./researchLabel.js";

export function ResearchAttribution() {
  return (
    <footer className="space-y-2 border-t border-line pt-3 text-sm">
      <p className="font-semibold">{RESEARCH_LABEL}</p>
      <p>{RESEARCH_CITATION}</p>
    </footer>
  );
}
