"use client";

import { Repeat } from "lucide-react";
import { SubmitButton } from "@/components/ui/submit-button";

export function SweepButton({ disabled = false }: { disabled?: boolean }) {
  return (
    <SubmitButton disabled={disabled} pendingLabel="Running sweep">
      <Repeat aria-hidden="true" />
      Run outreach sweep
    </SubmitButton>
  );
}
