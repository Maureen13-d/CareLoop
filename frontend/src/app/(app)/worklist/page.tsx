import { ArrowRight, CircleCheck, Flag, Hand, PhoneCall } from "lucide-react";
import { redirect } from "next/navigation";
import { Badge, Banner, EmptyState, Notice, Page, PageHeader, StatBar, controlClass, cx } from "@/components/ui";
import { SubmitButton } from "@/components/ui/submit-button";
import { api } from "@/lib/api";
import { stageShort } from "@/lib/format";
import { reasonTone, sentence } from "@/lib/status";
import type { Worklist } from "@/lib/types";
import { getSession } from "@/lib/session";
import { claimCase, escalateCase, logAttempt, recordOutcome } from "./actions";

export const instant = false;

export default async function WorklistPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const user = await getSession();
  if (!user) redirect("/login");
  if (!["chw", "navigator", "clinician", "admin", "program_manager"].includes(user.role)) {
    redirect("/");
  }
  const { error } = await searchParams;
  const data = await api<Worklist>("/followup/worklist");
  const canClaim = user.role === "chw";

  return (
    <Page>
      <PageHeader
        title="Who to chase"
        description="Ranked by urgency. A worsening report is always first. A late visit is a problem to solve, not the person’s fault."
        meta={
          <>
            <Badge tone="outline">Synthetic</Badge>
            <Badge tone="warn">{sentence(data.review.toLowerCase())}</Badge>
          </>
        }
      />

      <StatBar
        label="Chase list summary"
        items={[
          { label: "Open", value: data.counts.open },
          { label: "Overdue", value: data.counts.overdue, tone: data.counts.overdue ? "warn" : "default" },
          { label: "Reported worse", value: data.counts.worse, tone: data.counts.worse ? "danger" : "default" },
          { label: "Not reached", value: data.counts.unreached, tone: data.counts.unreached ? "warn" : "default" },
        ]}
      />

      {error ? <Notice tone="bad">{error}</Notice> : null}

      {data.rows.length === 0 ? (
        <EmptyState icon={<CircleCheck aria-hidden="true" />} title="No one to chase">
          Everyone with an ID has arrived, or is still within the time they were given.
        </EmptyState>
      ) : (
        <ol className="space-y-3" aria-label="People to chase, most urgent first">
          {data.rows.map((row, index) => {
            const tone = reasonTone(row.reason);
            return (
              <li
                key={row.public_id}
                className={cx(
                  "overflow-hidden rounded-2xl border bg-surface shadow-raised",
                  tone === "danger" ? "border-danger/30" : "border-line",
                )}
              >
                <div className="flex flex-col gap-4 p-5 lg:flex-row lg:items-start lg:justify-between">
                  <div className="flex min-w-0 gap-4">
                    <span
                      className={cx(
                        "flex size-9 shrink-0 items-center justify-center rounded-full text-sm font-semibold tabular-nums",
                        tone === "danger" ? "bg-danger text-white" : "bg-mint text-teal-text",
                      )}
                    >
                      <span className="sr-only">Rank </span>
                      {index + 1}
                    </span>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-lg font-semibold tracking-wide text-ink">{row.public_id}</p>
                        <Badge tone={tone}>{sentence(row.reason)}</Badge>
                      </div>
                      <p className="mt-1 text-sm text-ink-2">
                        Screened {row.days_since_screening} {row.days_since_screening === 1 ? "day" : "days"} ago. Now: {stageShort(row.state).toLowerCase()}.
                      </p>
                      <p className="mt-2 inline-flex items-center gap-1.5 text-[0.9375rem] font-medium text-ink">
                        <ArrowRight aria-hidden="true" className="size-4 text-teal-text" />
                        Next: {row.recommended_action}
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 lg:max-w-md lg:justify-end">
                    {canClaim ? (
                      <form action={claimCase}>
                        <input type="hidden" name="case_id" value={row.case_id} />
                        <SubmitButton variant="secondary" size="sm">
                          <Hand aria-hidden="true" />
                          Claim
                        </SubmitButton>
                      </form>
                    ) : null}
                    <form action={logAttempt}>
                      <input type="hidden" name="case_id" value={row.case_id} />
                      <SubmitButton variant="secondary" size="sm">
                        <PhoneCall aria-hidden="true" />
                        Log attempt
                      </SubmitButton>
                    </form>
                    <form action={escalateCase}>
                      <input type="hidden" name="case_id" value={row.case_id} />
                      <SubmitButton variant={tone === "danger" ? "primary" : "danger"} size="sm">
                        <Flag aria-hidden="true" />
                        Escalate
                      </SubmitButton>
                    </form>
                  </div>
                </div>
                <form action={recordOutcome} className="flex flex-wrap items-center gap-2 border-t border-line bg-canvas/60 px-5 py-3">
                  <input type="hidden" name="case_id" value={row.case_id} />
                  <label htmlFor={`outcome-${row.case_id}`} className="text-sm font-medium text-ink">
                    Outcome of the last contact
                  </label>
                  <select id={`outcome-${row.case_id}`} name="label" className={controlClass({ size: "sm", width: "auto" })}>
                    <option value="reached">Reached</option>
                    <option value="not_home">Not home</option>
                    <option value="barrier_noted">Barrier noted</option>
                  </select>
                  <SubmitButton variant="ghost" size="sm">
                    Save outcome
                  </SubmitButton>
                </form>
              </li>
            );
          })}
        </ol>
      )}

      <Banner>
        Ranks and actions come from fixed rules, not a model. Only a person can mark someone lost to follow-up, and
        only after an escalation exists.
      </Banner>
    </Page>
  );
}
