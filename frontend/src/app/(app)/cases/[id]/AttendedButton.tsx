"use client";

import { DoorOpen } from "lucide-react";
import { SubmitButton } from "@/components/ui/submit-button";

export function AttendedButton({ label }: { label: string }) {
  return (
    <SubmitButton pendingLabel="Saving">
      <DoorOpen aria-hidden="true" />
      {label}
    </SubmitButton>
  );
}
