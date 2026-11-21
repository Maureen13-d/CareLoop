"use client";

import { ArrowRight, Search } from "lucide-react";
import Link from "next/link";
import { useDeferredValue, useState } from "react";
import { Badge, EmptyState, JourneyMeter, Table, Td, Th, THead, Tr, controlClasses, cx } from "@/components/ui";
import { STAGE_ORDER, stageShort } from "@/lib/format";

export type CaseRow = {
  id: number;
  patient_ref: string | null;
  patient_display_name: string | null;
  state: string;
  state_label: string;
  urgency: string;
  owner_user_name: string | null;
  unowned: boolean;
  overdue: boolean;
  hours_overdue: number | null;
  open_escalations: number;
};

function Attention({ row }: { row: CaseRow }) {
  if (row.overdue) return <Badge tone="warn">{row.hours_overdue}h past deadline</Badge>;
  if (row.open_escalations) return <Badge tone="danger">Escalated</Badge>;
  return <Badge tone="teal">On time</Badge>;
}

function Progress({ state }: { state: string }) {
  const index = STAGE_ORDER.indexOf(state as (typeof STAGE_ORDER)[number]);
  if (index === -1) return null;
  return <JourneyMeter total={STAGE_ORDER.length} reached={index + 1} className="mt-2 w-32" />;
}

/** The case list, with a search over the cases already loaded for this filter. */
export function CaseList({ rows }: { rows: CaseRow[] }) {
  const [query, setQuery] = useState("");
  const deferred = useDeferredValue(query);
  const needle = deferred.trim().toLowerCase();
  const shown = needle
    ? rows.filter((row) =>
        [row.patient_display_name, row.patient_ref, row.owner_user_name, stageShort(row.state)]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(needle)),
      )
    : rows;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="relative w-full sm:max-w-xs">
          <label htmlFor="case-search" className="sr-only">
            Search by name, reference, owner or step
          </label>
          <Search aria-hidden="true" className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-ink-3" />
          <input
            id="case-search"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search name, reference or owner"
            className={cx(controlClasses, "pl-10")}
          />
        </div>
        <p className="text-sm text-ink-2" aria-live="polite">
          {shown.length} of {rows.length} {rows.length === 1 ? "case" : "cases"}
        </p>
      </div>

      {shown.length === 0 ? (
        <EmptyState icon={<Search aria-hidden="true" />} title="No case matches">
          Try a name, a CL reference, or an owner. Search covers the cases in this view.
        </EmptyState>
      ) : (
        <>
          {/* tablets and desktops */}
          <Table caption="Cases in this view" className="hidden md:block">
            <THead>
              <Th>Person</Th>
              <Th>Step</Th>
              <Th>Owner</Th>
              <Th>Attention</Th>
              <Th>
                <span className="sr-only">Open</span>
              </Th>
            </THead>
            <tbody>
              {shown.map((row) => (
                <Tr key={row.id}>
                  <Td>
                    <Link href={`/desk/${row.id}`} className="font-medium text-ink hover:text-teal-text hover:underline">
                      {row.patient_display_name}
                    </Link>
                    <span className="mt-0.5 block text-ink-2">{row.patient_ref}</span>
                  </Td>
                  <Td>
                    <span className="inline-flex flex-wrap items-center gap-2">
                      <span className="font-medium text-ink">{stageShort(row.state)}</span>
                      {row.urgency === "urgent" ? <Badge tone="danger">Urgent</Badge> : null}
                    </span>
                    <Progress state={row.state} />
                  </Td>
                  <Td className={row.owner_user_name ? "text-ink" : "text-ink-2"}>{row.owner_user_name ?? "No owner yet"}</Td>
                  <Td>
                    <Attention row={row} />
                  </Td>
                  <Td className="text-right">
                    <Link
                      href={`/desk/${row.id}`}
                      aria-label={`Open ${row.patient_display_name ?? "case"}`}
                      className="inline-flex size-9 items-center justify-center rounded-full text-teal-text hover:bg-mint"
                    >
                      <ArrowRight aria-hidden="true" className="size-4" />
                    </Link>
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>

          {/* phones */}
          <ul className="space-y-3 md:hidden">
            {shown.map((row) => (
              <li key={row.id}>
                <Link
                  href={`/desk/${row.id}`}
                  className="block rounded-2xl border border-line bg-surface p-4 shadow-raised hover:border-teal"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="font-medium text-ink">{row.patient_display_name}</p>
                      <p className="text-sm text-ink-2">{row.patient_ref}</p>
                    </div>
                    <Attention row={row} />
                  </div>
                  <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
                    <span className="font-medium text-ink">{stageShort(row.state)}</span>
                    {row.urgency === "urgent" ? <Badge tone="danger">Urgent</Badge> : null}
                    <span className="text-ink-2">{row.owner_user_name ? `with ${row.owner_user_name}` : "no owner yet"}</span>
                  </div>
                  <Progress state={row.state} />
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
