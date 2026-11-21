"use client";

import { ErrorPanel } from "@/components/ui/error-panel";

export default function OutreachError({ reset }: { reset: () => void }) {
  return (
    <ErrorPanel
      title="Outreach unavailable"
      message="Could not reach the CareLoop API. Check that the backend is running, then try again."
      reset={reset}
    />
  );
}
