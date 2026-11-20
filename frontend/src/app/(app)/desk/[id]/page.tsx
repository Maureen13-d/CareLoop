import Link from "next/link";
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
import { completeTask } from "../task-actions";
import { Notice } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { FACILITIES, STAGE_ORDER, formatWhen, stageShort } from "@/lib/format";
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

type Task = {
  id: number;
  case_id: number | null;
  title: string;
  summary: string;
  priority: string;
  status: string;
};

const button =
  "rounded-full bg-lagoon px-4 py-2 text-sm text-white hover:bg-lagoon-deep disabled:opacity-50";
const quiet = "rounded-full border border-line bg-white px-4 py-2 text-sm hover:border-lagoon";

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
    <div className="space-y-3 rounded-2xl border border-line bg-white p-4">
      <h3 className="text-xl">Simulated clinic</h3>
      <p className="text-sm text-ink-soft">
        This talks to the pretend hospital on port 8100. It is not a real clinic, and the
        message does not name a finding.
      </p>
      {link ? (
        <p className="text-sm">
          Visit {link.appointment_id} at {link.location_ref}.
          {link.milestones.length
            ? ` The clinic has reported: ${link.milestones.join(", ")}.`
            : " Nothing reported yet."}
        </p>
      ) : (
        <p className="text-sm">No visit has been sent yet.</p>
      )}
      <div className="flex flex-wrap gap-2">
        {!link && canRequest ? (
          <form action={requestVisit}>
            <input type="hidden" name="caseId" value={caseId} />
            <button className={button}>Send the visit request</button>
          </form>
        ) : null}
        {link && !finished ? (
          <form action={advanceClinic}>
            <input type="hidden" name="caseId" value={caseId} />
            <button className={quiet}>Record the clinic's next milestone</button>
          </form>
        ) : null}
      </div>
    </div>
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
    api<Task[]>("/navigator/tasks?status=open&limit=100"),
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
    <main className="space-y-8 px-4 py-6 md:px-0 md:py-0">
      <nav aria-label="Breadcrumb">
        <Link href="/desk" className="text-sm text-lagoon underline underline-offset-2">
          All cases
        </Link>
      </nav>
      {notice ? <Notice tone="ok">{notice}</Notice> : null}
      {error ? <Notice tone="bad">{error}</Notice> : null}

      <header className="space-y-3">
        <p className="text-sm text-lagoon">{detail.patient_ref}</p>
        <h1 className="text-4xl">{detail.patient_display_name}</h1>
        <p className="max-w-2xl text-lg text-ink-soft">{detail.state_label}</p>
        <div className="flex flex-wrap gap-2 text-sm">
          <span className="rounded-full bg-lagoon px-3 py-1 text-white">{stageShort(detail.state)}</span>
          {detail.urgency === "urgent" ? (
            <span className="rounded-full bg-[#f8e8e4] px-3 py-1 text-danger">Urgent</span>
          ) : null}
          {detail.overdue ? (
            <span className="rounded-full bg-[#f8efd4] px-3 py-1 text-clay">
              {detail.hours_overdue}h past an assumed deadline
            </span>
          ) : null}
          <span className="rounded-full border border-line px-3 py-1">
            {detail.owner_user_name ? `Owner: ${detail.owner_user_name}` : "No owner yet"}
          </span>
        </div>
      </header>

      <ol aria-label="Pathway" className="flex flex-wrap gap-2">
        {stageOrder.map((name) => {
          const index = stageOrder.indexOf(name);
          const here = stageOrder.indexOf(detail.state);
          const done = here > index;
          const current = name === detail.state;
          return (
            <li
              key={name}
              aria-current={current ? "step" : undefined}
              className={`rounded-full border px-3 py-1 text-sm ${
                current
                  ? "border-lagoon bg-lagoon text-white"
                  : done
                    ? "border-moss text-moss"
                    : "border-line text-ink-soft"
              }`}
            >
              {done ? "✓ " : ""}
              {stageShort(name)}
            </li>
          );
        })}
      </ol>

      <div className="grid gap-8 lg:grid-cols-[1fr_0.9fr]">
        <section aria-labelledby="do-heading" className="space-y-4">
          <h2 id="do-heading" className="text-2xl">
            What you can do
          </h2>
          {terminal ? (
            <p>This journey is finished{detail.closure_reason ? `: ${detail.closure_reason.replaceAll("_", " ")}` : ""}.</p>
          ) : (
            <div className="space-y-4 rounded-2xl border border-line bg-paper-2 p-4">
              {detail.unowned ? (
                <form action={claimCase}>
                  <input type="hidden" name="caseId" value={detail.id} />
                  <button className={button}>I’ll take this case</button>
                </form>
              ) : null}
              {next.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {next.map((target) => (
                    <form key={target} action={moveCase}>
                      <input type="hidden" name="caseId" value={detail.id} />
                      <input type="hidden" name="toState" value={target} />
                      <button className={button}>Move to {stageShort(target)}</button>
                    </form>
                  ))}
                </div>
              ) : null}
              {canClose ? (
                <form action={closeCase} className="space-y-2">
                  <input type="hidden" name="caseId" value={detail.id} />
                  <label className="block text-sm" htmlFor="evidence_type">
                    Close with evidence
                  </label>
                  <select id="evidence_type" name="evidence_type" className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm">
                    <option value="facility_confirmation">Facility confirmed care started</option>
                    <option value="follow_up_plan_documented">Follow-up plan documented</option>
                    <option value="clinician_decision">Clinician decision</option>
                  </select>
                  <input
                    name="description"
                    required
                    placeholder="What evidence did you record?"
                    className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm"
                  />
                  <button className={button}>Close the loop</button>
                </form>
              ) : (
                <form action={declineCase} className="space-y-2">
                  <label className="block text-sm" htmlFor="decline-note">
                    They chose not to continue
                  </label>
                  <input
                    id="decline-note"
                    name="note"
                    required
                    placeholder="What they decided, in your words"
                    className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm"
                  />
                  <input type="hidden" name="caseId" value={detail.id} />
                  <button className={quiet}>Record that choice</button>
                </form>
              )}
              {detail.open_escalations > 0 ? (
                <form action={markLost} className="space-y-2">
                  <label className="block text-sm" htmlFor="lost-note">
                    Lost to follow-up is a human decision
                  </label>
                  <input
                    id="lost-note"
                    name="note"
                    required
                    placeholder="What was tried, and why you are closing"
                    className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm"
                  />
                  <input type="hidden" name="caseId" value={detail.id} />
                  <button className={quiet}>Record lost to follow-up</button>
                </form>
              ) : null}
              <p className="text-xs text-ink-soft">
                Deadlines are marked {pathway.deadlines_status}. They are not taken from a national guideline.
                {detail.deadline_at ? ` This step is due ${formatWhen(detail.deadline_at)} UTC.` : ""}
              </p>
            </div>
          )}

          {showFacilities ? (
            <div>
              <h3 className="text-xl">Places a navigator can suggest</h3>
              <ul className="mt-2 space-y-2">
                {FACILITIES.map((place) => (
                  <li key={place.name} className="rounded-2xl border border-line bg-white px-4 py-3">
                    <p className="font-medium">{place.name}</p>
                    <p className="text-sm text-ink-soft">{place.note}</p>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <ClinicCard caseId={detail.id} state={detail.state} pathwayId={detail.pathway_id} />
          {maternal ? <MaternalPanel caseId={detail.id} /> : null}

          {mine.length > 0 ? (
            <div className="space-y-3">
              <h3 className="text-xl">Escalations</h3>
              {mine.map((item) => (
                <form key={item.id} action={resolveEscalation} className="space-y-2 rounded-2xl border border-clay/40 bg-[#f8efd4] p-4">
                  <p className="text-sm">
                    Level {item.level} · {item.reason}
                  </p>
                  <input type="hidden" name="caseId" value={detail.id} />
                  <input type="hidden" name="escalationId" value={item.id} />
                  <input name="note" required placeholder="What you did" className="w-full rounded-xl border border-line bg-white px-3 py-2 text-sm" />
                  <button className={button}>Resolve</button>
                </form>
              ))}
            </div>
          ) : null}

          {myTasks.length > 0 ? (
            <div className="space-y-3">
              <h3 className="text-xl">Tasks</h3>
              {myTasks.map((task) => (
                <form key={task.id} action={completeTask} className="rounded-2xl border border-line bg-white p-4">
                  <p className="font-medium">{task.title}</p>
                  <p className="text-sm text-ink-soft">{task.summary}</p>
                  <input type="hidden" name="taskId" value={task.id} />
                  <input type="hidden" name="back" value={`/desk/${detail.id}`} />
                  <button className={`${button} mt-3`}>Mark done</button>
                </form>
              ))}
            </div>
          ) : null}
        </section>

        <section aria-labelledby="timeline-heading">
          <h2 id="timeline-heading" className="text-2xl">
            Timeline
          </h2>
          <ol className="mt-4 space-y-4 border-l border-line pl-4">
            {timeline.map((event) => (
              <li key={event.id}>
                <p className="font-medium">
                  {event.from_state ? `${stageShort(event.from_state)} → ` : ""}
                  {stageShort(event.to_state)}
                </p>
                <p className="text-sm text-ink-soft">
                  {formatWhen(event.occurred_at)} UTC · {event.actor_name ?? event.actor_type}
                </p>
                {event.note ? <p className="text-sm">{event.note}</p> : null}
              </li>
            ))}
          </ol>
        </section>
      </div>
    </main>
  );
}
