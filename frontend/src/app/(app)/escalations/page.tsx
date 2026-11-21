import { CircleCheck } from "lucide-react";
import Link from "next/link";
import { redirect } from "next/navigation";
import { completeTask } from "@/app/(app)/desk/task-actions";
import { Badge, ButtonLink, Card, EmptyState, Notice, Page, PageHeader, SectionHeader, StatBar } from "@/components/ui";
import { SubmitButton } from "@/components/ui/submit-button";
import { ApiError, api } from "@/lib/api";
import { formatWhen } from "@/lib/format";
import { priorityLabel, priorityTone, sentence } from "@/lib/status";
import type { NavigatorTask } from "@/lib/types";
import { getSession } from "@/lib/session";

export const instant = false;

const NAMED = new Set(["navigator", "clinician", "counsellor", "chw", "admin"]);
const CASE_ROLES = new Set(["navigator", "clinician"]);
const CAN_COMPLETE = new Set(["navigator", "clinician", "counsellor"]);
const COUNTS = new Set(["program_manager"]);

/** The guide opens these. Seeded demo handoffs use "system" for the same kind of task. */
const GUIDE_SOURCES = new Set(["assistant", "followup", "telegram", "channel", "checkin", "system"]);

const SOURCE_LABEL: Record<string, string> = {
  assistant: "Support chat",
  followup: "Follow-up guide",
  telegram: "Telegram",
  channel: "Basic phone",
  checkin: "Check-in",
  system: "Guide",
  device: "Cuff hub",
};

type CaseRow = {
  id: number;
  patient_ref: string | null;
  patient_display_name: string | null;
};

type Escalation = {
  id: number;
  case_id: number;
  patient_ref: string | null;
  level: number;
  reason: string;
  raised_at: string;
};

type Summary = {
  open_tasks: number;
  open_escalations: number;
};

type Item = {
  key: string;
  name: string;
  ref: string | null;
  href: string | null;
  tasks: NavigatorTask[];
  escalations: Escalation[];
};

function sourceLabel(source: string | undefined): string {
  if (!source) return "Guide";
  return SOURCE_LABEL[source] ?? sentence(source);
}

export default async function EscalationsPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role === "patient") redirect("/chat");
  const { error } = await searchParams;
  const canOpen = CASE_ROLES.has(user.role);
  const canList = canOpen || user.role === "admin";
  const canComplete = CAN_COMPLETE.has(user.role);

  if (COUNTS.has(user.role)) {
    let summary: Summary | null = null;
    let problem: string | null = null;
    try {
      summary = await api<Summary>("/analytics/summary");
    } catch (err) {
      problem = err instanceof ApiError ? err.message : "The counts could not load.";
    }
    return (
      <Page>
        <PageHeader
          title="Escalated cases"
          description="Counts only. Names, worries and the person’s own words stay with the navigator and the counsellor."
        />
        {error ? <Notice tone="bad">{error}</Notice> : null}
        {problem ? <Notice tone="bad">{problem}</Notice> : null}
        {summary ? (
          <StatBar
            label="What is waiting"
            items={[
              { label: "Open tasks", value: summary.open_tasks },
              {
                label: "Open escalations",
                value: summary.open_escalations,
                tone: summary.open_escalations ? "danger" : "default",
              },
            ]}
          />
        ) : null}
      </Page>
    );
  }

  if (!NAMED.has(user.role)) {
    return (
      <Page>
        <PageHeader
          title="Escalated cases"
          description="The navigator sees the cases the guide handed over. This account reviews clips, not those conversations."
        />
        <Card as="section" aria-labelledby="review-heading">
          <SectionHeader
            id="review-heading"
            title="Clip review stays here"
            description="A signed line plays for a patient only after review. The guide’s handoffs are not on this account."
          />
          <div className="mt-5">
            <ButtonLink href="/ksl">Open clip review</ButtonLink>
          </div>
        </Card>
      </Page>
    );
  }

  let tasks: NavigatorTask[] = [];
  let cases: CaseRow[] = [];
  let escalations: Escalation[] = [];
  let problem: string | null = null;
  try {
    if (canList) {
      [tasks, cases, escalations] = await Promise.all([
        api<NavigatorTask[]>("/navigator/tasks?status=open&limit=100"),
        api<CaseRow[]>("/cases?status=open&limit=100"),
        api<Escalation[]>("/escalations?resolved=false&limit=100"),
      ]);
    } else {
      tasks = await api<NavigatorTask[]>("/navigator/tasks?status=open&limit=100");
    }
  } catch (err) {
    problem = err instanceof ApiError ? err.message : "Escalated cases could not load.";
  }

  const caseById = new Map(cases.map((row) => [row.id, row]));
  const items = new Map<string, Item>();

  function ensure(caseId: number | null, seed?: { name?: string | null; ref?: string | null }): Item {
    const key = caseId == null ? `loose-${seed?.name ?? "none"}-${items.size}` : `case-${caseId}`;
    const found = caseId == null ? undefined : items.get(key);
    if (found) return found;
    const row = caseId != null ? caseById.get(caseId) : undefined;
    const named = row?.patient_display_name ?? seed?.name ?? null;
    const ref = row?.patient_ref ?? seed?.ref ?? null;
    const item: Item = {
      key: caseId == null ? `loose-${items.size}` : key,
      name: named ?? ref ?? "No case linked yet",
      ref: named ? ref : null,
      href: caseId != null && canOpen ? `/desk/${caseId}` : null,
      tasks: [],
      escalations: [],
    };
    items.set(item.key, item);
    return item;
  }

  for (const task of tasks) {
    // A red hub reading is escalated. A yellow one stays a note on the navigator's Today page.
    const redReading = task.source === "device" && task.priority === "urgent";
    if (!GUIDE_SOURCES.has(task.source ?? "") && !redReading) continue;
    const item =
      task.case_id == null
        ? ensure(null, { name: task.patient_display_name, ref: task.patient_ref })
        : ensure(task.case_id, { name: task.patient_display_name, ref: task.patient_ref });
    if (task.patient_display_name && (item.name === "No case linked yet" || item.name === task.patient_ref)) {
      item.ref = task.patient_ref ?? item.ref;
      item.name = task.patient_display_name;
    }
    if (!item.ref && task.patient_ref && task.patient_ref !== item.name) item.ref = task.patient_ref;
    item.tasks.push(task);
  }

  for (const escalation of escalations) {
    const item = ensure(escalation.case_id, { ref: escalation.patient_ref });
    if (!item.ref) item.ref = escalation.patient_ref;
    item.escalations.push(escalation);
  }

  const list = [...items.values()].sort((a, b) => {
    const urgent = (item: Item) =>
      item.tasks.some((task) => task.priority === "urgent" || task.priority === "high") ||
      item.escalations.some((escalation) => escalation.level > 1)
        ? 0
        : 1;
    return urgent(a) - urgent(b);
  });

  return (
    <Page>
      <PageHeader
        title="Escalated by the guide"
        description="Cases the guide handed to a person, from the chat, the phone, Telegram, a check-in or a red cuff hub reading. The person’s own words are not on this list."
        meta={<Badge tone={list.length ? "danger" : "neutral"}>{list.length} waiting</Badge>}
      />
      {error ? <Notice tone="bad">{error}</Notice> : null}
      {problem ? <Notice tone="bad">{problem}</Notice> : null}
      {!problem && list.length === 0 ? (
        <EmptyState icon={<CircleCheck aria-hidden="true" />} title="Nothing handed over">
          When someone confirms a worry, or the guide stops and asks for a person, the case appears here.
        </EmptyState>
      ) : null}
      {list.length > 0 ? (
        <Card padded={false} as="section" aria-labelledby="handoff-heading">
          <SectionHeader
            id="handoff-heading"
            title="Waiting for a person"
            description="Open a case to agree the next step. Mark a task done once you have done it."
            className="px-5 pt-5"
          />
          <ul className="mt-4 divide-y divide-line border-t border-line">
            {list.map((item) => (
              <li key={item.key} className="space-y-3 px-5 py-4">
                <div className="flex flex-wrap items-center gap-2">
                  {item.href ? (
                    <Link href={item.href} className="font-medium text-ink underline-offset-2 hover:text-teal-text hover:underline">
                      {item.name}
                    </Link>
                  ) : (
                    <p className="font-medium text-ink">{item.name}</p>
                  )}
                  {item.ref ? <span className="text-sm text-ink-2">{item.ref}</span> : null}
                  {item.escalations.length > 0 ? <Badge tone="danger">Escalated</Badge> : null}
                </div>
                {item.escalations.map((escalation) => (
                  <p key={escalation.id} className="text-sm text-ink-2">
                    Level {escalation.level}. {escalation.reason}. Raised {formatWhen(escalation.raised_at)} UTC.
                  </p>
                ))}
                <ul className="space-y-3">
                  {item.tasks.map((task) => (
                    <li key={task.id} className="flex flex-col gap-3 rounded-xl bg-canvas px-4 py-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-medium text-ink">{task.title}</p>
                          <Badge tone="outline">{sourceLabel(task.source)}</Badge>
                          {task.priority !== "normal" ? (
                            <Badge tone={priorityTone(task.priority)}>{priorityLabel(task.priority)}</Badge>
                          ) : null}
                        </div>
                        <p className="mt-1 text-sm text-ink-2">{task.summary}</p>
                      </div>
                      {canComplete ? (
                        <form action={completeTask} className="shrink-0">
                          <input type="hidden" name="taskId" value={task.id} />
                          <input type="hidden" name="back" value="/escalations" />
                          <SubmitButton variant="secondary" size="sm" pendingLabel="Saving">
                            Mark done
                          </SubmitButton>
                        </form>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </Card>
      ) : null}
    </Page>
  );
}
