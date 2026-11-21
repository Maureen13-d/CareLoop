import { ArrowRight, CircleCheck, FilePlus, FolderOpen, ListChecks, MapPin, ScrollText, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { redirect } from "next/navigation";
import { PathwayFunnel } from "@/components/PathwayFunnel";
import { TaskItem } from "@/components/TaskItem";
import {
  Badge,
  ButtonLink,
  Card,
  EmptyState,
  Notice,
  Page,
  SectionHeader,
  StatBar,
  type StatItem,
  buttonClasses,
} from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { formatWhen, stageShort } from "@/lib/format";
import { reasonTone, riskTone, sentence } from "@/lib/status";
import type { NavigatorTask, Worklist } from "@/lib/types";
import { getSession } from "@/lib/session";

export const instant = false;

type Summary = {
  open_cases: number;
  overdue: number;
  unowned: number;
  open_escalations: number;
  open_tasks: number;
  handed_off: number;
  deadlines_status: string;
};

type Funnel = {
  pathway_name: string;
  deadlines_status: string;
  stages: { state: string; label: string; count: number }[];
  terminals: { state: string; label: string; count: number }[];
};

type CaseRow = {
  id: number;
  patient_ref: string | null;
  patient_display_name: string | null;
  state: string;
  urgency: string;
  owner_user_name: string | null;
  unowned: boolean;
  overdue: boolean;
  hours_overdue: number | null;
};

type MaternalSummary = {
  open: number;
  red: number;
  yellow: number;
  unowned: number;
  device_alerts: number;
  sos_24h: number;
  red_cases: { case_id: number; display_name: string; patient_ref: string; hours_left: number | null; state: string }[];
  review: string;
};

type Woman = {
  id: number;
  patient_ref: string;
  display_name: string;
  gestation_band: string;
  area_label: string;
  case_state: string | null;
  urgency: string | null;
  risk_level: string | null;
};

type AuditRow = {
  id: number;
  occurred_at: string;
  role: string | null;
  action: string;
  entity_type: string;
  entity_id: number | null;
  outcome: string;
};

const CASE_ROLES = new Set(["navigator", "clinician"]);
const TASK_ROLES = new Set(["navigator", "clinician", "counsellor", "admin"]);
const CHASE_ROLES = new Set(["navigator", "clinician", "admin", "program_manager"]);
const AUDIT_ROLES = new Set(["admin", "program_manager"]);
const MATERNAL_ROLES = new Set(["navigator", "clinician", "program_manager", "admin"]);

/** The dark band at the top of the dashboard. */
function Hero({ title, line, actions }: { title: string; line: string; actions?: React.ReactNode }) {
  return (
    <section className="on-dark relative overflow-hidden rounded-[1.75rem] bg-emerald px-6 pt-8 pb-20 text-white sm:px-10 sm:pt-10 sm:pb-24">
      <svg
        aria-hidden="true"
        viewBox="0 0 400 400"
        className="pointer-events-none absolute -top-24 -right-24 size-[26rem] text-white/[0.06] sm:-right-10"
      >
        <circle cx="200" cy="200" r="150" fill="none" stroke="currentColor" strokeWidth="44" />
        <circle cx="200" cy="200" r="88" fill="none" stroke="currentColor" strokeWidth="2" />
      </svg>
      <div className="relative max-w-2xl">
        <h1 className="text-[2rem] leading-tight text-white sm:text-[2.5rem]">{title}</h1>
        <p className="mt-3 text-[1.0625rem] leading-relaxed text-on-dark/85">{line}</p>
        {actions ? <div className="mt-6 flex flex-wrap gap-2">{actions}</div> : null}
      </div>
    </section>
  );
}

function ChasePreview({ worklist }: { worklist: Worklist }) {
  const rows = worklist.rows.slice(0, 4);
  return (
    <Card padded={false} as="section" aria-labelledby="chase-heading">
      <SectionHeader
        id="chase-heading"
        title="Who to chase next"
        description="The top of the ranked follow-up list. A worsening report is always first."
        action={
          <ButtonLink href="/worklist" variant="ghost" size="sm">
            Full list
            <ArrowRight aria-hidden="true" />
          </ButtonLink>
        }
        className="px-5 pt-5"
      />
      {rows.length === 0 ? (
        <div className="p-5">
          <EmptyState icon={<CircleCheck aria-hidden="true" />} title="No one to chase">
            Everyone with an ID has arrived or is on time.
          </EmptyState>
        </div>
      ) : (
        <ol className="mt-4 divide-y divide-line border-t border-line">
          {rows.map((row, index) => (
            <li key={row.public_id} className="flex items-start gap-4 px-5 py-3.5">
              <span className="mt-0.5 w-5 text-sm font-semibold tabular-nums text-ink-3">{index + 1}</span>
              <div className="min-w-0 flex-1">
                <p className="font-medium tracking-wide text-ink">{row.public_id}</p>
                <p className="mt-0.5 text-sm text-ink-2">
                  Screened {row.days_since_screening} {row.days_since_screening === 1 ? "day" : "days"} ago. Next: {row.recommended_action}
                </p>
              </div>
              <Badge tone={reasonTone(row.reason)} className="mt-0.5">
                {sentence(row.reason)}
              </Badge>
            </li>
          ))}
        </ol>
      )}
    </Card>
  );
}

async function ChwHome({ first }: { first: string }) {
  let women: Woman[] = [];
  let problem: string | null = null;
  try {
    women = await api<Woman[]>("/maternal/pregnancies");
  } catch (err) {
    problem = err instanceof ApiError ? err.message : "Your list could not load.";
  }
  let worklist: Worklist | null = null;
  try {
    worklist = await api<Worklist>("/followup/worklist");
  } catch {
    worklist = null;
  }

  return (
    <Page>
      <div>
        <Hero
          title={`Hello, ${first}.`}
          line="These are the women assigned to you. A colour is a label for the navigator, not a diagnosis. Synthetic demo, pending clinical review."
          actions={
            <ButtonLink href="/worklist" variant="on-dark">
              <ListChecks aria-hidden="true" />
              Who to chase
            </ButtonLink>
          }
        />
        {worklist ? (
          <StatBar
            label="Your follow-up list"
            className="relative mx-3 -mt-12 sm:mx-6"
            items={[
              { label: "Open", value: worklist.counts.open },
              { label: "Overdue", value: worklist.counts.overdue, tone: worklist.counts.overdue ? "warn" : "default" },
              { label: "Reported worse", value: worklist.counts.worse, tone: worklist.counts.worse ? "danger" : "default" },
              { label: "Not reached", value: worklist.counts.unreached },
            ]}
          />
        ) : null}
      </div>

      {problem ? <Notice tone="bad">{problem}</Notice> : null}

      <Card padded={false} as="section" aria-labelledby="women-heading">
        <SectionHeader
          id="women-heading"
          title="Women assigned to you"
          description="Open a name to record a home check, a cuff reading or a band."
          className="px-5 pt-5"
        />
        {women.length === 0 && !problem ? (
          <div className="p-5">
            <EmptyState title="No one is assigned to you yet">A clinician assigns women when they issue an ID.</EmptyState>
          </div>
        ) : (
          <ul className="mt-4 divide-y divide-line border-t border-line">
            {women.map((woman) => (
              <li key={woman.id}>
                <Link href={`/chw/${woman.id}`} className="group flex items-center gap-4 px-5 py-4 hover:bg-canvas/60">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-ink group-hover:text-teal-text">{woman.display_name}</p>
                    <p className="mt-0.5 flex flex-wrap gap-x-3 text-sm text-ink-2">
                      <span>{woman.patient_ref}</span>
                      <span className="inline-flex items-center gap-1">
                        <MapPin aria-hidden="true" className="size-3.5" />
                        {woman.area_label}
                      </span>
                      <span>{woman.gestation_band}</span>
                    </p>
                  </div>
                  <div className="hidden flex-wrap justify-end gap-1.5 sm:flex">
                    <Badge tone="outline">{woman.case_state ? stageShort(woman.case_state) : "No journey yet"}</Badge>
                    {woman.urgency === "urgent" ? <Badge tone="danger">Urgent</Badge> : null}
                    <Badge tone={riskTone(woman.risk_level)}>{woman.risk_level ? `Label ${woman.risk_level}` : "No reading yet"}</Badge>
                  </div>
                  <ArrowRight aria-hidden="true" className="size-4 shrink-0 text-ink-3" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {worklist ? <ChasePreview worklist={worklist} /> : null}
    </Page>
  );
}

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role === "patient") redirect("/chat");
  if (user.role === "chw") {
    return <ChwHome first={user.display_name.split(" ")[0]} />;
  }
  const { error } = await searchParams;

  let summary: Summary | null = null;
  let funnel: Funnel | null = null;
  let cases: CaseRow[] = [];
  let tasks: NavigatorTask[] = [];
  let problem: string | null = null;

  try {
    summary = await api<Summary>("/analytics/summary");
    funnel = await api<Funnel>("/analytics/funnel");
    if (CASE_ROLES.has(user.role)) {
      cases = await api<CaseRow[]>("/cases?status=open&limit=100");
    }
    if (TASK_ROLES.has(user.role)) {
      tasks = await api<NavigatorTask[]>("/navigator/tasks?status=open&limit=20");
    }
  } catch (err) {
    problem = err instanceof ApiError ? err.message : "The desk could not load.";
  }

  let maternal: MaternalSummary | null = null;
  if (MATERNAL_ROLES.has(user.role)) {
    try {
      maternal = await api<MaternalSummary>("/maternal/summary");
    } catch {
      maternal = null;
    }
  }

  let worklist: Worklist | null = null;
  if (CHASE_ROLES.has(user.role)) {
    try {
      worklist = await api<Worklist>("/followup/worklist");
    } catch {
      worklist = null;
    }
  }

  let activity: AuditRow[] = [];
  if (AUDIT_ROLES.has(user.role)) {
    try {
      activity = await api<AuditRow[]>("/audit?limit=6");
    } catch {
      activity = [];
    }
  }

  const first = user.display_name.split(" ")[0];
  const attention = cases.filter((item) => item.overdue || item.unowned).slice(0, 6);

  const stats: StatItem[] = summary
    ? [
        { label: "Open journeys", value: summary.open_cases },
        {
          label: "Past deadline",
          value: summary.overdue,
          hint: `Deadlines are ${summary.deadlines_status.toLowerCase()}`,
          tone: summary.overdue ? "warn" : "default",
        },
        { label: "Waiting for an owner", value: summary.unowned, tone: summary.unowned ? "warn" : "default" },
        { label: "Open tasks", value: summary.open_tasks },
      ]
    : [];

  const line = summary
    ? `${summary.open_cases} ${summary.open_cases === 1 ? "person is" : "people are"} on the pathway. ${summary.overdue} ${summary.overdue === 1 ? "is" : "are"} past the assumed deadline.`
    : "The navigation desk shows who is waiting, and what a person can do next.";

  const heroActions = (
    <>
      {CASE_ROLES.has(user.role) ? (
        <ButtonLink href="/desk" variant="on-dark">
          <FolderOpen aria-hidden="true" />
          Open cases
        </ButtonLink>
      ) : null}
      {user.role === "clinician" ? (
        <Link href="/intake" className={buttonClasses({ variant: "on-dark-outline" })}>
          <FilePlus aria-hidden="true" />
          Open a case
        </Link>
      ) : null}
      {CHASE_ROLES.has(user.role) ? (
        <Link href="/worklist" className={buttonClasses({ variant: "on-dark-outline" })}>
          <ListChecks aria-hidden="true" />
          Who to chase
        </Link>
      ) : null}
      {AUDIT_ROLES.has(user.role) ? (
        <Link href="/audit" className={buttonClasses({ variant: "on-dark-outline" })}>
          <ScrollText aria-hidden="true" />
          Audit trail
        </Link>
      ) : null}
    </>
  );

  return (
    <Page>
      <div>
        <Hero title={`Hello, ${first}.`} line={line} actions={heroActions} />
        {stats.length ? <StatBar label="Summary" items={stats} className="relative mx-3 -mt-12 sm:mx-6" /> : null}
      </div>

      {error ? <Notice tone="bad">{error}</Notice> : null}
      {problem ? <Notice tone="bad">{problem}</Notice> : null}

      {funnel ? (
        <Card as="section" aria-labelledby="funnel-heading">
          <SectionHeader
            id="funnel-heading"
            title="Where people are"
            description={`Open journeys at each step of the ${funnel.pathway_name.toLowerCase()} pathway. Deadlines are ${funnel.deadlines_status.toLowerCase()}.`}
          />
          <div className="mt-6">
            <PathwayFunnel
              caption="Number of people at each pathway step"
              stages={funnel.stages.map((stage) => ({ id: stage.state, label: stageShort(stage.state), count: stage.count }))}
            />
          </div>
          {funnel.terminals.length ? (
            <div className="mt-6 flex flex-wrap items-center gap-2 border-t border-line pt-4">
              <span className="text-sm text-ink-2">Finished journeys</span>
              {funnel.terminals.map((item) => (
                <Badge key={item.state} tone="outline">
                  {stageShort(item.state)} <span className="font-semibold tabular-nums text-ink">{item.count}</span>
                </Badge>
              ))}
            </div>
          ) : null}
        </Card>
      ) : null}

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]">
        {TASK_ROLES.has(user.role) ? (
          <Card padded={false} as="section" aria-labelledby="tasks-heading">
            <SectionHeader
              id="tasks-heading"
              title="Needs a person"
              description="Confirmed worries, handoffs and missed steps land here."
              action={<Badge tone={tasks.length ? "teal" : "neutral"}>{tasks.length} open</Badge>}
              className="px-5 pt-5"
            />
            {tasks.length === 0 ? (
              <div className="p-5">
                <EmptyState icon={<CircleCheck aria-hidden="true" />} title="No open tasks">
                  When someone confirms a worry or asks for a person, it appears here.
                </EmptyState>
              </div>
            ) : (
              <ul className="mt-4 divide-y divide-line border-t border-line">
                {tasks.map((task) => (
                  <TaskItem key={task.id} task={task} back="/" />
                ))}
              </ul>
            )}
          </Card>
        ) : (
          <Card padded={false} as="section" aria-labelledby="activity-heading">
            <SectionHeader
              id="activity-heading"
              title="Recent activity"
              description="From the audit trail. A person’s own words are never written there."
              action={
                AUDIT_ROLES.has(user.role) ? (
                  <ButtonLink href="/audit" variant="ghost" size="sm">
                    Audit trail
                    <ArrowRight aria-hidden="true" />
                  </ButtonLink>
                ) : undefined
              }
              className="px-5 pt-5"
            />
            <div className="mx-5 mt-4 flex gap-3 rounded-xl bg-mint px-4 py-3 text-sm text-teal-text">
              <ShieldCheck aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
              You see counts and events only. Names, worries and chat stay with the navigator and the counsellor.
            </div>
            {activity.length ? (
              <ul className="mt-4 divide-y divide-line border-t border-line">
                {activity.map((row) => (
                  <li key={row.id} className="flex items-start justify-between gap-4 px-5 py-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-ink">{sentence(row.action.replaceAll(".", " "))}</p>
                      <p className="text-[0.8125rem] text-ink-2">
                        {row.role ? sentence(row.role) : "System"}, {row.entity_type}
                        {row.entity_id ? ` ${row.entity_id}` : ""}
                      </p>
                    </div>
                    <time dateTime={row.occurred_at} className="shrink-0 text-[0.8125rem] text-ink-2">
                      {formatWhen(row.occurred_at)}
                    </time>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="p-5">
                <EmptyState title="No activity to show">Events appear here as people use CareLoop.</EmptyState>
              </div>
            )}
          </Card>
        )}

        {CASE_ROLES.has(user.role) ? (
          <Card padded={false} as="section" aria-labelledby="attention-heading">
            <SectionHeader
              id="attention-heading"
              title="Journeys to open"
              description="Past their deadline, or waiting for an owner."
              action={
                <ButtonLink href="/desk" variant="ghost" size="sm">
                  All cases
                  <ArrowRight aria-hidden="true" />
                </ButtonLink>
              }
              className="px-5 pt-5"
            />
            {attention.length === 0 ? (
              <div className="p-5">
                <EmptyState icon={<CircleCheck aria-hidden="true" />} title="Nothing waiting">
                  No journey is overdue or without an owner.
                </EmptyState>
              </div>
            ) : (
              <ul className="mt-4 divide-y divide-line border-t border-line">
                {attention.map((item) => (
                  <li key={item.id}>
                    <Link href={`/desk/${item.id}`} className="group flex items-center gap-3 px-5 py-3.5 hover:bg-canvas/60">
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-ink group-hover:text-teal-text">{item.patient_display_name}</p>
                        <p className="mt-0.5 text-sm text-ink-2">
                          {item.patient_ref}, {stageShort(item.state).toLowerCase()}
                          {item.owner_user_name ? `, with ${item.owner_user_name}` : ""}
                        </p>
                      </div>
                      {item.overdue ? (
                        <Badge tone="warn">{item.hours_overdue}h over</Badge>
                      ) : (
                        <Badge tone="outline">No owner</Badge>
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        ) : worklist ? (
          <ChasePreview worklist={worklist} />
        ) : null}
      </div>

      {CASE_ROLES.has(user.role) && worklist ? <ChasePreview worklist={worklist} /> : null}

      {maternal ? (
        <Card as="section" aria-labelledby="maternal-heading">
          <SectionHeader
            id="maternal-heading"
            title="Maternal checks"
            description={`${sentence(maternal.review.toLowerCase())}. Counts are synthetic. A colour is a label for decision support, not a diagnosis.`}
          />
          <StatBar
            label="Maternal checks"
            className="mt-5"
            flat
            items={[
              { label: "Open maternal journeys", value: maternal.open },
              { label: "Red labels", value: maternal.red, tone: maternal.red ? "danger" : "default", hint: "Decision support only" },
              { label: "Yellow labels", value: maternal.yellow, tone: maternal.yellow ? "warn" : "default" },
              { label: "Device alerts", value: maternal.device_alerts, hint: `${maternal.sos_24h} SOS in the last 24 hours` },
            ]}
          />
          {maternal.red_cases.length > 0 && CASE_ROLES.has(user.role) ? (
            <ul className="mt-5 divide-y divide-line overflow-hidden rounded-xl border border-line">
              {maternal.red_cases.map((item) => (
                <li key={item.case_id}>
                  <Link href={`/desk/${item.case_id}`} className="group flex items-center gap-3 px-4 py-3 hover:bg-canvas/60">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-ink group-hover:text-teal-text">{item.display_name}</p>
                      <p className="text-sm text-ink-2">
                        {item.patient_ref}, {stageShort(item.state).toLowerCase()}
                      </p>
                    </div>
                    <Badge tone="danger">Label red</Badge>
                    <span className="w-16 text-right text-sm font-medium tabular-nums text-danger">
                      {item.hours_left ?? "–"}h left
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : null}
        </Card>
      ) : null}
    </Page>
  );
}
