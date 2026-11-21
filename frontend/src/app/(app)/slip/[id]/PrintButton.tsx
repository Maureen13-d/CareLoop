"use client";

import { Printer } from "lucide-react";
import { buttonClasses } from "@/components/ui/button";

export function PrintButton() {
  return (
    <button type="button" onClick={() => window.print()} className={buttonClasses({ variant: "primary" })}>
      <Printer aria-hidden="true" />
      Print the card
    </button>
  );
}
