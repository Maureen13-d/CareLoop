import { CircleCheck } from "lucide-react";
import Link from "next/link";
import { fmtStage, fmtTime } from "@/components/OutreachKind";
import { Badge, EmptyState, SectionHeader, Table, Td, Th, THead, Tr } from "@/components/ui";
import { getEscalated } from "@/lib/outreach-api";

export async function EscalatedSection() {
  const escalated = await getEscalated();
  return (
    <section aria-labelledby="escalated-heading" className="space-y-3">
      <SectionHeader
        id="escalated-heading"
        title="Awaiting a care coordinator"
        description="Automated outreach is exhausted. A person needs to step in."
        action={escalated.length ? <Badge tone="danger">{escalated.length} waiting</Badge> : undefined}
      />
      {escalated.length === 0 ? (
        <EmptyState icon={<CircleCheck aria-hidden="true" />} title="No escalated cases" />
      ) : (
        <Table caption="Cases where automated outreach is exhausted, most overdue first">
          <THead>
            <Th>Case</Th>
            <Th>Patient</Th>
            <Th>Stage</Th>
            <Th>Days overdue</Th>
            <Th>Escalated (UTC)</Th>
          </THead>
          <tbody>
            {escalated.map((e) => (
              <Tr key={e.case_id}>
                <Td>
                  <Link href={`/cases/${e.case_id}`} className="font-medium text-teal-text hover:underline">
                    {e.case_id}
                  </Link>
                </Td>
                <Td>{e.patient_ref}</Td>
                <Td>{fmtStage(e.stage)}</Td>
                <Td>
                  <Badge tone="danger">{e.days_overdue} days</Badge>
                </Td>
                <Td className="whitespace-nowrap text-ink-2">
                  <time dateTime={e.escalated_at}>{fmtTime(e.escalated_at)}</time>
                </Td>
              </Tr>
            ))}
          </tbody>
        </Table>
      )}
    </section>
  );
}
