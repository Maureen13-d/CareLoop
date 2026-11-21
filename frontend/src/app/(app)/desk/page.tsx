import { FilePlus } from "lucide-react";
import { redirect } from "next/navigation";
import { CaseList, type CaseRow } from "./CaseList";
import { ButtonLink, EmptyState, FilterTabs, Notice, Page, PageHeader } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { getSession } from "@/lib/session";

export const instant = false;

const FILTERS = [
  { id: "open", label: "Open" },
  { id: "overdue", label: "Past deadline" },
  { id: "unowned", label: "No owner" },
  { id: "all", label: "Everything" },
] as const;

const EMPTY: Record<string, string> = {
  open: "No journeys are open. A case opens when a clinician records a concerning finding with consent.",
  overdue: "No open journey is past its assumed deadline.",
  unowned: "Every open journey has an owner.",
  all: "No cases have been recorded yet.",
};

function queryFor(filter: string): string {
  if (filter === "overdue") return "/cases?status=open&overdue=true&limit=100";
  if (filter === "unowned") return "/cases?status=open&unowned=true&limit=100";
  if (filter === "all") return "/cases?status=all&limit=100";
  return "/cases?status=open&limit=100";
}

export default async function DeskPage({
  searchParams,
}: {
  searchParams: Promise<{ filter?: string }>;
}) {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role !== "navigator" && user.role !== "clinician") redirect("/");
  const { filter = "open" } = await searchParams;
  const active = FILTERS.some((item) => item.id === filter) ? filter : "open";

  let cases: CaseRow[] = [];
  let problem: string | null = null;
  try {
    cases = await api<CaseRow[]>(queryFor(active));
  } catch (error) {
    problem = error instanceof ApiError ? error.message : "Cases could not be loaded.";
  }

  return (
    <Page>
      <PageHeader
        title="Everyone on the pathway"
        description="A case opens when a clinician records a concerning finding and the person has agreed to be contacted. Names here are synthetic."
        actions={
          user.role === "clinician" ? (
            <ButtonLink href="/intake" variant="primary">
              <FilePlus aria-hidden="true" />
              Open a case
            </ButtonLink>
          ) : undefined
        }
      />
      <FilterTabs
        label="Filter cases"
        active={active}
        items={FILTERS.map((item) => ({
          id: item.id,
          label: item.label,
          href: item.id === "open" ? "/desk" : `/desk?filter=${item.id}`,
        }))}
      />
      {problem ? <Notice tone="bad">{problem}</Notice> : null}
      {!problem && cases.length === 0 ? (
        <EmptyState title="No cases in this view">{EMPTY[active]}</EmptyState>
      ) : null}
      {cases.length > 0 ? <CaseList key={active} rows={cases} /> : null}
    </Page>
  );
}
