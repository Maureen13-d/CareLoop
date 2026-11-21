import { ArrowRight, Building, CircleCheck, Hospital, MapPin, UserPlus } from "lucide-react";
import { notFound, redirect } from "next/navigation";
import {
  advanceClinic,
  claimCase,
  closeCase,
  declineCase,
  markLost,
  moveCase,
  requestVisit,
  resolveEscalation,
} from "./actions";
import { MaternalPanel } from "./MaternalPanel";
import { TaskItem } from "@/components/TaskItem";
import {
  Badge,
  Card,
  Field,
  Input,
  JourneyStepper,
  Notice,
  Page,
  PageHeader,
  SectionHeader,
  Select,
  Timeline,
  TimelineItem,
} from "@/components/ui";
import { SubmitButton } from "@/components/ui/submit-button";
import { ApiError, api } from "@/lib/api";
import { FACILITIES, STAGE_ORDER, formatWhen, stageShort } from "@/lib/format";
import { sentence } from "@/lib/status";
import type { NavigatorTask } from "@/lib/types";
import { getSession } from "@/lib/session";

export const instant = false;

type CaseDetail = {
  id: number;
  patient_ref: string | null;
  patient_display_name: string | null;
  pathway_id: string;
  state: string;
  state_label: string;
  urgency: string;
  owner_user_name: string | null;
  owner_department: string | null;
  unowned: boolean;
  overdue: boolean;
  hours_overdue: number | null;
  deadline_at: string | null;
  open_escalations: number;
  state_entered_at: string;
  closure_reason: string | null;
};

type TimelineEvent = {
  id: number;
  from_state: string | null;
  to_state: string;
  actor_name: string | null;
  actor_type: string;
  occurred_at: string;
  note: string | null;
};

type Pathway = {
  states: { name: string; label: string; next: string[] }[];
  terminal_states: Record<string, string>;
  deadlines_status: string;
};

type Escalation = {
  id: number;
  case_id: number;
  level: number;
  reason: string;
  raised_at: string;
  resolved_at: string | null;
};

async function ClinicCard({
  caseId,
  state,
  pathwayId,
}: {
  caseId: number;
  state: string;
  pathwayId: string;
}) {
  let link: { appointment_id: string; milestones: string[]; location_ref: string } | null = null;
  try {
    link = await api(`/cases/${caseId}/hospital`);
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 404) throw error;
  }
  const canRequest =
    pathwayId === "maternal"
      ? state === "navigating" || state === "visit_booked" || state === "delivery_planned"
      : state === "NAVIGATION_ACTIVE" || state === "APPOINTMENT_BOOKED";
  if (!link && !canRequest) return null;
  const finished = (link?.milestones.length ?? 0) >= 3;
  return (
    <Card as="section" aria-labelledby="clinic-heading">
      <SectionHeader
        id="clinic-heading"
        title="Visit request to the clinic"
        description="Sent as FHIR to the simulated hospital on port 8100. It is not a real clinic, and the message does not name a finding."
        action={<Badge tone="outline">Simulated</Badge>}
      />
      <div className="mt-4 flex gap-3 rounded-xl bg-canvas px-4 py-3">
        <Hospital aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-teal-text" />
        {link ? (
          <div className="text-sm">
            <p className="font-medium text-ink">
              Visit {link.appointment_id} at {link.location_ref}
            </p>
            {link.milestones.length ? (
              <ul className="mt-2 flex flex-wrap gap-1.5" aria-label="Milestones the clinic reported">
                {link.milestones.map((milestone) => (
                  <li key={milestone}>
                    <Badge tone="teal" icon={<CircleCheck aria-hidden="true" />}>
                      {sentence(milestone)}
                    </Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-0.5 text-ink-2">The clinic has not reported anything yet.</p>
            )}
          </div>
        ) : (
          <p className="text-sm text-ink-2">No visit request has been sent yet.</p>
        )}
      </div>
      {(!link && canRequest) || (link && !finished) ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {!link && canRequest ? (
            <form action={requestVisit}>
              <input type="hidden" name="caseId" value={caseId} />
              <SubmitButton pendingLabel="Sending">Send the visit request</SubmitButton>
            </form>
          ) : null}
          {link && !finished ? (
            <form action={advanceClinic}>
              <input type="hidden" name="caseId" value={caseId} />
              <SubmitButton variant="secondary" pendingLabel="Recording">
                Record the clinic’s next milestone
              </SubmitButton>
            </form>
          ) : null}
        </div>
      ) : null}
    </Card>
  );
}

export default async function CaseWorkspace({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ notice?: string; error?: string }>;
}) {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role !== "navigator" && user.role !== "clinician") redirect("/");

  const { id } = await params;
  const { notice, error } = await searchParams;
  if (!/^\d+$/.test(id)) notFound();

  let detail: CaseDetail;
  try {
    detail = await api<CaseDetail>(`/cases/${id}`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const [timeline, pathway, escalations, tasks] = await Promise.all([
    api<TimelineEvent[]>(`/cases/${id}/timeline`),
    api<Pathway>(`/pathways/${detail.pathway_id}`),
    api<Escalation[]>("/escalations?resolved=false&limit=100"),
    api<NavigatorTask[]>("/navigator/tasks?status=open&limit=100"),
  ]);

  const state = pathway.states.find((item) => item.name === detail.state);
  const next = state?.next ?? [];
  const terminal = detail.state in pathway.terminal_states;
  const mine = escalations.filter((item) => item.case_id === detail.id);
  const myTasks = tasks.filter((item) => item.case_id === detail.id);
  const maternal = detail.pathway_id === "maternal";
  const stageOrder = maternal ? pathway.states.map((item) => item.name) : [...STAGE_ORDER];
  const showFacilities =
    detail.state === "NAVIGATION_ACTIVE" ||
    detail.state === "APPOINTMENT_BOOKED" ||
    detail.state === "navigating" ||
    detail.state === "visit_booked";
  const canClose = detail.state === "HANDED_OFF" || detail.state === "with_hospital" || detail.state === "postnatal_watch";

  return (
    <Page>
      <PageHeader
        back={{ href: "/desk", label: "All cases" }}
        title={detail.patient_display_name ?? "Case"}
        description={detail.state_label}
        meta={
          <>
            {detail.patient_ref ? <Badge tone="outline">{detail.patient_ref}</Badge> : null}
            <Badge tone="solid">{stageShort(detail.state)}</Badge>
            {detail.urgency === "urgent" ? <Badge tone="danger">Urgent</Badge> : null}
            {detail.overdue ? <Badge tone="warn">{detail.hours_overdue}h past an assumed deadline</Badge> : null}
            {detail.open_escalations > 0 ? <Badge tone="danger">Escalated</Badge> : null}
            <Badge tone={detail.owner_user_name ? "teal" : "neutral"}>
              {detail.owner_user_name ? `Owner: ${detail.owner_user_name}` : "No owner yet"}
            </Badge>
          </>
        }
      />

      {notice ? <Notice tone="ok">{notice}</Notice> : null}
      {error ? <Notice tone="bad">{error}</Notice> : null}

      <Card as="section" aria-label="Pathway progress">
        <JourneyStepper
          steps={stageOrder.map((name) => ({ id: name, label: stageShort(name) }))}
          current={detail.state}
          finished={terminal}
        />
      </Card>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,22rem)]">
        <div className="space-y-6">
          <Card as="section" aria-labelledby="do-heading">
            <SectionHeader
              id="do-heading"
              title={terminal ? "This journey is finished" : "Next steps"}
              description={
                terminal
                  ? detail.closure_reason
                    ? `Closed: ${detail.closure_reason.replaceAll("_", " ")}.`
                    : undefined
                  : "Clinical decisions stay with a qualified person. Every step you take is recorded on the timeline."
              }
            />
            {!terminal ? (
              <div className="mt-5 space-y-6">
                {detail.unowned ? (
                  <form action={claimCase} className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-mint px-4 py-3">
                    <p className="text-sm text-teal-text">Nobody owns this journey yet.</p>
                    <input type="hidden" name="caseId" value={detail.id} />
                    <SubmitButton size="sm" pendingLabel="Claiming">
                      <UserPlus aria-hidden="true" />
                      I’ll take this case
                    </SubmitButton>
                  </form>
                ) : null}

                {next.length > 0 ? (
                  <div>
                    <p className="text-sm font-medium text-ink">Move the journey on</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {next.map((target, index) => (
                        <form key={target} action={moveCase}>
                          <input type="hidden" name="caseId" value={detail.id} />
                          <input type="hidden" name="toState" value={target} />
                          <SubmitButton variant={index === 0 ? "primary" : "secondary"} pendingLabel="Moving">
                            Move to {stageShort(target)}
                            <ArrowRight aria-hidden="true" />
                          </SubmitButton>
                        </form>
                      ))}
                    </div>
                  </div>
                ) : null}

                {canClose ? (
                  <form action={closeCase} className="space-y-4 border-t border-line pt-5">
                    <input type="hidden" name="caseId" value={detail.id} />
                    <p className="text-sm font-medium text-ink">Close the loop with evidence</p>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field label="Evidence" htmlFor="evidence_type">
                        <Select id="evidence_type" name="evidence_type">
                          <option value="facility_confirmation">Facility confirmed care started</option>
                          <option value="follow_up_plan_documented">Follow-up plan documented</option>
                          <option value="clinician_decision">Clinician decision</option>
                        </Select>
                      </Field>
                      <Field label="What you recorded" htmlFor="close-description">
                        <Input id="close-description" name="description" required placeholder="What evidence did you record?" />
                      </Field>
                    </div>
                    <SubmitButton pendingLabel="Closing">Close the loop</SubmitButton>
                  </form>
                ) : (
                  <form action={declineCase} className="space-y-3 border-t border-line pt-5">
                    <Field
                      label="They chose not to continue"
                      htmlFor="decline-note"
                      hint="Their choice is respected and recorded. Write what they decided, in your words."
                    >
                      <Input id="decline-note" name="note" required placeholder="What they decided" aria-describedby="decline-note-hint" />
                    </Field>
                    <input type="hidden" name="caseId" value={detail.id} />
                    <SubmitButton variant="secondary" pendingLabel="Recording">
                      Record that choice
                    </SubmitButton>
                  </form>
                )}

                {detail.open_escalations > 0 ? (
                  <form action={markLost} className="space-y-3 border-t border-line pt-5">
                    <Field
                      label="Lost to follow-up"
                      htmlFor="lost-note"
                      hint="This is always a human decision. Say what was tried, and why you are closing."
                    >
                      <Input id="lost-note" name="note" required placeholder="What was tried" aria-describedby="lost-note-hint" />
                    </Field>
                    <input type="hidden" name="caseId" value={detail.id} />
                    <SubmitButton variant="danger" pendingLabel="Recording">
                      Record lost to follow-up
                    </SubmitButton>
                  </form>
                ) : null}

                <p className="border-t border-line pt-4 text-[0.8125rem] text-ink-2">
                  Deadlines are marked {pathway.deadlines_status.toLowerCase()}. They are not taken from a national guideline.
                  {detail.deadline_at ? ` This step is due ${formatWhen(detail.deadline_at)} UTC.` : ""}
                </p>
              </div>
            ) : null}
          </Card>

          {mine.length > 0 ? (
            <Card as="section" aria-labelledby="escalations-heading" tone="danger">
              <SectionHeader
                id="escalations-heading"
                title="Escalations"
                description="A missed step that needs a person. Say what you did to resolve it."
              />
              <ul className="mt-4 space-y-3">
                {mine.map((item) => (
                  <li key={item.id} className="rounded-xl border border-danger/20 bg-danger-bg/50 p-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone="danger">Level {item.level}</Badge>
                      <p className="text-sm font-medium text-ink">{item.reason}</p>
                    </div>
                    <p className="mt-1 text-[0.8125rem] text-ink-2">Raised {formatWhen(item.raised_at)} UTC</p>
                    <form action={resolveEscalation} className="mt-3 flex flex-col gap-2 sm:flex-row">
                      <input type="hidden" name="caseId" value={detail.id} />
                      <input type="hidden" name="escalationId" value={item.id} />
                      <label htmlFor={`resolve-${item.id}`} className="sr-only">
                        What you did
                      </label>
                      <Input id={`resolve-${item.id}`} name="note" required placeholder="What you did" className="sm:flex-1" />
                      <SubmitButton pendingLabel="Resolving">Resolve</SubmitButton>
                    </form>
                  </li>
                ))}
              </ul>
            </Card>
          ) : null}

          {myTasks.length > 0 ? (
            <Card padded={false} as="section" aria-labelledby="tasks-heading">
              <SectionHeader id="tasks-heading" title="Open tasks for this person" className="px-5 pt-5" />
              <ul className="mt-4 divide-y divide-line border-t border-line">
                {myTasks.map((task) => (
                  <TaskItem key={task.id} task={task} back={`/desk/${detail.id}`} showPerson={false} />
                ))}
              </ul>
            </Card>
          ) : null}

          <ClinicCard caseId={detail.id} state={detail.state} pathwayId={detail.pathway_id} />

          {showFacilities ? (
            <Card as="section" aria-labelledby="places-heading">
              <SectionHeader
                id="places-heading"
                title="Places a navigator can suggest"
                description="Synthetic places for the demo. Ask about the fee before the person travels."
              />
              <ul className="mt-4 grid gap-3 sm:grid-cols-3">
                {FACILITIES.map((place) => (
                  <li key={place.name} className="rounded-xl border border-line p-4">
                    <Building aria-hidden="true" className="size-5 text-teal-text" />
                    <p className="mt-2 font-medium text-ink">{place.name}</p>
                    <p className="mt-1 text-sm text-ink-2">{place.note}</p>
                  </li>
                ))}
              </ul>
            </Card>
          ) : null}

          {maternal ? (
            <Card as="div">
              <MaternalPanel caseId={detail.id} />
            </Card>
          ) : null}
        </div>

        <Card as="section" aria-labelledby="timeline-heading" className="lg:sticky lg:top-6">
          <SectionHeader id="timeline-heading" title="Timeline" description="Every step, who took it, and when (UTC)." />
          <div className="mt-5">
            {timeline.length === 0 ? (
              <p className="text-sm text-ink-2">Nothing recorded yet.</p>
            ) : (
              <Timeline label="Case timeline">
                {timeline.map((event, index) => (
                  <TimelineItem
                    key={event.id}
                    tone={index === timeline.length - 1 ? "ok" : "default"}
                    title={
                      event.from_state
                        ? `${stageShort(event.from_state)} to ${stageShort(event.to_state)}`
                        : stageShort(event.to_state)
                    }
                    meta={`${formatWhen(event.occurred_at)}, ${event.actor_name ?? event.actor_type}`}
                  >
                    {event.note}
                  </TimelineItem>
                ))}
              </Timeline>
            )}
          </div>
          {detail.owner_department ? (
            <p className="mt-5 flex items-center gap-2 border-t border-line pt-4 text-[0.8125rem] text-ink-2">
              <MapPin aria-hidden="true" className="size-4" />
              Owned by {detail.owner_department}
            </p>
          ) : null}
        </Card>
      </div>
    </Page>
  );
}
