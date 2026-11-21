"use client";

import { ErrorPanel } from "@/components/ui/error-panel";

export default function CaseError({ reset }: { reset: () => void }) {
  return (
    <ErrorPanel
      title="Case unavailable"
      message="Could not load or update this case. Check the backend, then try again."
      reset={reset}
    />
  );
}
