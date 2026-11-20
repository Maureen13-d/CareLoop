import Link from "next/link";
import { redirect } from "next/navigation";
import { completeTask } from "./desk/task-actions";
import { Banner, Notice, Stat } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { stageShort } from "@/lib/format";
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

type Task = {
  id: number;
  case_id: number | null;
  patient_display_name: string | null;
  patient_ref: string | null;
  priority: string;
  title: string;
  summary: string;
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

async function ChwHome({ first }: { first: string }) {
  let women: Woman[] = [];
  let problem: string | null = null;
  try {
    women = await api<Woman[]>("/maternal/pregnancies");
  } catch (err) {
    problem = err instanceof ApiError ? err.message : "Your list could not load.";
  }

  return (
    <main className="space-y-8 px-4 py-6 md:px-0 md:py-0">
      <header className="max-w-2xl">
        <p className="text-sm text-lagoon">Today</p>
        <h1 className="mt-1 text-4xl">Hello, {first}.</h1>
        <p className="mt-3 text-lg leading-relaxed text-ink-soft">
          These are the women assigned to you. A colour is a label for the navigator, not a diagnosis.
          Synthetic demo. PENDING CLINICAL REVIEW.
        </p>
      </header>
      {problem ? <Notice tone="bad">{problem}</Notice> : null}
      {women.length === 0 && !problem ? (
        <p className="text-sm text-ink-soft">No women are assigned to you yet.</p>
      ) : (
        <ul className="divide-y divide-line rounded-2xl border border-line bg-paper-2">
          {women.map((woman) => (
            <li key={woman.id} className="px-4 py-4">
              <Link href={`/chw/${woman.id}`} className="text-base font-medium text-lagoon underline underline-offset-2">
                {woman.display_name}
              </Link>
              <p className="mt-1 text-sm text-ink-soft">
                {woman.patient_ref} · {woman.area_label} · {woman.gestation_band}
              </p>
              <p className="mt-2 text-sm">
                {woman.case_state ? stageShort(woman.case_state) : "No journey yet"}
                {woman.urgency === "urgent" ? " · Urgent" : ""}
                {" · "}
                {woman.risk_level ? `Reading ${woman.risk_level}` : "No reading yet"}
              </p>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

const CASE_ROLES = new Set(["navigator", "clinician"]);
const TASK_ROLES = new Set(["navigator", "clinician", "counsellor"]);

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
  let tasks: Task[] = [];
  let problem: string | null = null;

  try {
    summary = await api<Summary>("/analytics/summary");
    funnel = await api<Funnel>("/analytics/funnel");
    if (CASE_ROLES.has(user.role)) {
      cases = await api<CaseRow[]>("/cases?status=open&limit=100");
    }
    if (TASK_ROLES.has(user.role)) {
      tasks = await api<Task[]>("/navigator/tasks?status=open&limit=20");
    }
  } catch (err) {
    problem = err instanceof ApiError ? err.message : "The desk could not load.";
  }

  let maternal: MaternalSummary | null = null;
  if (user.role === "navigator" || user.role === "clinician" || user.role === "program_manager" || user.role === "admin") {
    try {
      maternal = await api<MaternalSummary>("/maternal/summary");
    } catch {
      maternal = null;
    }
  }

  const first = user.display_name.split(" ")[0];
  const max = Math.max(1, ...(funnel?.stages.map((stage) => stage.count) ?? [1]));
  const attention = cases.filter((item) => item.overdue || item.unowned).slice(0, 6);

  return (
    <main className="space-y-8 px-4 py-6 md:px-0 md:py-0">
      <header className="max-w-2xl">
        <p className="text-sm text-lagoon">Today</p>
        <h1 className="mt-1 text-4xl">Hello, {first}.</h1>
        <p className="mt-3 text-lg leading-relaxed text-ink-soft">
          {summary
            ? `${summary.open_cases} ${summary.open_cases === 1 ? "person is" : "people are"} on the pathway. ${summary.overdue} ${summary.overdue === 1 ? "is" : "are"} past the assumed deadline.`
            : "The navigation desk shows who is waiting, and what a person can do next."}
        </p>
      </header>

      {error ? <Notice tone="bad">{error}</Notice> : null}
      {problem ? <Notice tone="bad">{problem}</Notice> : null}

      {summary ? (
        <section aria-label="Summary" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label="Open journeys" value={summary.open_cases} />
          <Stat label="Past deadline" value={summary.overdue} hint="Deadlines are assumed" />
          <Stat label="Waiting for an owner" value={summary.unowned} />
          <Stat label="Open tasks" value={summary.open_tasks} />
        </section>
      ) : null}

      {maternal ? (
        <section aria-label="Maternal checks" className="space-y-3">
          <h2 className="text-2xl">Maternal checks</h2>
          <p className="text-sm text-ink-soft">{maternal.review}. Counts are synthetic.</p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Stat label="Open maternal journeys" value={maternal.open} />
            <Stat label="Red labels" value={maternal.red} hint="Decision support only" />
            <Stat label="Yellow labels" value={maternal.yellow} />
            <Stat label="Device alerts" value={maternal.device_alerts} hint={`${maternal.sos_24h} SOS in 24h`} />
          </div>
          {maternal.red_cases.length > 0 ? (
            <ul className="divide-y divide-line rounded-2xl border border-line bg-paper-2">
              {maternal.red_cases.map((item) => (
                <li key={item.case_id}>
                  <Link href={`/desk/${item.case_id}`} className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-white">
                    <span>
                      <span className="block font-medium">{item.display_name}</span>
                      <span className="text-sm text-ink-soft">{item.patient_ref} · {stageShort(item.state)} · label red</span>
                    </span>
                    <span className="text-sm text-danger">{item.hours_left ?? "—"}h left</span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      {funnel ? (
        <section aria-labelledby="funnel-heading" className="space-y-3">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <h2 id="funnel-heading" className="text-2xl">
              Where people are
            </h2>
            <p className="text-xs uppercase tracking-wide text-ink-soft">
              {funnel.deadlines_status} deadlines
            </p>
          </div>
          <ol className="grid gap-2 sm:grid-cols-4 lg:grid-cols-7">
            {funnel.stages.map((stage) => (
              <li key={stage.state} className="rounded-2xl border border-line bg-paper-2 p-3">
                <p className="font-serif text-3xl text-lagoon">{stage.count}</p>
                <p className="mt-1 text-sm font-medium">{stageShort(stage.state)}</p>
                <div className="mt-3 h-1.5 rounded-full bg-line" aria-hidden="true">
                  <div
                    className="h-full rounded-full bg-lagoon"
                    style={{ width: `${Math.max(8, (stage.count / max) * 100)}%` }}
                  />
                </div>
              </li>
            ))}
          </ol>
          <p className="text-sm text-ink-soft">
            Closed journeys:{" "}
            {funnel.terminals.map((item) => `${stageShort(item.state)} ${item.count}`).join(" · ")}
          </p>
        </section>
      ) : null}

      <div className="grid gap-8 lg:grid-cols-2">
        {TASK_ROLES.has(user.role) ? (
          <section aria-labelledby="tasks-heading" className="space-y-3">
            <h2 id="tasks-heading" className="text-2xl">
              Needs a person
            </h2>
            {tasks.length === 0 ? (
              <p className="text-sm text-ink-soft">No open tasks. Confirmed worries and handoffs land here.</p>
            ) : (
              <ul className="space-y-3">
                {tasks.map((task) => (
                  <li key={task.id} className="rounded-2xl border border-line bg-paper-2 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium">{task.title}</p>
                        <p className="mt-1 text-sm text-ink-soft">{task.summary}</p>
                        {task.case_id ? (
                          <Link href={`/desk/${task.case_id}`} className="mt-2 inline-block text-sm text-lagoon underline underline-offset-2">
                            {task.patient_display_name} · {task.patient_ref}
                          </Link>
                        ) : (
                          <p className="mt-2 text-sm text-ink-soft">From the phone or the chat. No case linked yet.</p>
                        )}
                      </div>
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-medium ${
                          task.priority === "urgent"
                            ? "bg-[#f8e8e4] text-danger"
                            : task.priority === "high"
                              ? "bg-[#f8efd4] text-clay"
                              : "bg-white text-ink-soft"
                        }`}
                      >
                        {task.priority}
                      </span>
                    </div>
                    <form action={completeTask} className="mt-3">
                      <input type="hidden" name="taskId" value={task.id} />
                      <input type="hidden" name="back" value="/" />
                      <button className="rounded-full bg-lagoon px-3 py-1.5 text-sm text-white hover:bg-lagoon-deep">
                        Mark done
                      </button>
                    </form>
                  </li>
                ))}
              </ul>
            )}
          </section>
        ) : (
          <Banner>
            You are seeing counts only. Names, worries and chat stay with the navigator and the counsellor.
          </Banner>
        )}

        {CASE_ROLES.has(user.role) ? (
          <section aria-labelledby="attention-heading" className="space-y-3">
            <h2 id="attention-heading" className="text-2xl">
              Journeys to open
            </h2>
            {attention.length === 0 ? (
              <p className="text-sm text-ink-soft">Nothing is overdue or unowned.</p>
            ) : (
              <ul className="divide-y divide-line rounded-2xl border border-line bg-paper-2">
                {attention.map((item) => (
                  <li key={item.id}>
                    <Link href={`/desk/${item.id}`} className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-white">
                      <span>
                        <span className="block font-medium">{item.patient_display_name}</span>
                        <span className="text-sm text-ink-soft">
                          {item.patient_ref} · {stageShort(item.state)}
                          {item.owner_user_name ? ` · ${item.owner_user_name}` : " · no owner"}
                        </span>
                      </span>
                      <span className="text-sm text-clay">
                        {item.overdue ? `${item.hours_overdue}h over` : "Unowned"}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
            <Link href="/desk" className="inline-block text-sm text-lagoon underline underline-offset-2">
              All cases
            </Link>
          </section>
        ) : null}
      </div>
    </main>
  );
}
