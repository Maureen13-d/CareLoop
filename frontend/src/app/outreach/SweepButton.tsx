"use client";

import { useFormStatus } from "react-dom";

export function SweepButton({ disabled = false }: { disabled?: boolean }) {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending || disabled}
      aria-busy={pending}
      className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-700 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {pending ? "Running sweep…" : "Run outreach sweep"}
    </button>
  );
}
