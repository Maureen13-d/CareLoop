import { Check, PhoneCall } from "lucide-react";
import Link from "next/link";
import { completeTask } from "@/app/(app)/desk/task-actions";
import { Badge } from "@/components/ui";
import { SubmitButton } from "@/components/ui/submit-button";
import { priorityLabel, priorityTone } from "@/lib/status";
import type { NavigatorTask } from "@/lib/types";

/** One open navigator task, with the person it concerns and a way to mark it done. */
export function TaskItem({ task, back, showPerson = true }: { task: NavigatorTask; back: string; showPerson?: boolean }) {
  return (
    <li className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-medium text-ink">{task.title}</p>
          {task.priority !== "normal" ? <Badge tone={priorityTone(task.priority)}>{priorityLabel(task.priority)}</Badge> : null}
        </div>
        <p className="mt-1 text-sm text-ink-2">{task.summary}</p>
        {showPerson ? (
          task.case_id ? (
            <Link
              href={`/desk/${task.case_id}`}
              className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-teal-text underline-offset-2 hover:underline"
            >
              {task.patient_display_name ?? "Open the case"}
              {task.patient_ref ? <span className="font-normal text-ink-2">({task.patient_ref})</span> : null}
            </Link>
          ) : (
            <p className="mt-2 text-sm text-ink-2">From the phone or the chat. No case linked yet.</p>
          )
        ) : null}
        {task.contact_ref ? (
          <p className="mt-1 inline-flex items-center gap-1.5 text-sm text-ink-2">
            <PhoneCall aria-hidden="true" className="size-3.5" />
            Call back on {task.contact_ref}
          </p>
        ) : null}
      </div>
      <form action={completeTask} className="shrink-0">
        <input type="hidden" name="taskId" value={task.id} />
        <input type="hidden" name="back" value={back} />
        <SubmitButton variant="secondary" size="sm" pendingLabel="Saving">
          <Check aria-hidden="true" />
          Mark done
        </SubmitButton>
      </form>
    </li>
  );
}
