import { ArrowUpRight, Camera, CircleCheck, FlaskConical, Hand } from "lucide-react";
import Link from "next/link";
import { redirect } from "next/navigation";
import {
  Badge,
  ButtonLink,
  Card,
  EmptyState,
  Notice,
  Page,
  PageHeader,
  SectionHeader,
  StatBar,
  Table,
  Td,
  Th,
  THead,
  Tr,
  type Tone,
} from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { getSession } from "@/lib/session";

export const instant = false;

type ClipRow = {
  id: number;
  template_id: string;
  label: string;
  status: string;
  pilot_enabled: boolean;
  video_uri?: string | null;
};

const STATUS: Record<string, { label: string; tone: Tone }> = {
  uploaded: { label: "Waiting for review", tone: "warn" },
  approved: { label: "Approved", tone: "teal" },
  stale: { label: "Stale: phrase changed", tone: "danger" },
  retired: { label: "Retired", tone: "neutral" },
};

// The order the backend enforces before a clip can be approved (see backend/app/modules/ksl/review.py).
const STEPS = [
  ["Uploaded", "An editor uploads a recorded clip for one approved phrase."],
  ["Deaf review", "A Deaf reviewer watches it and passes or fails it."],
  ["Back-translation", "A second person, not the Deaf reviewer, passes a back-translation."],
  ["Approval", "Someone who is neither the uploader nor a reviewer approves it."],
];

function labelTone(label: string): Tone {
  return label.toUpperCase().includes("NOT") ? "warn" : "outline";
}

export default async function KslReviewPage() {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role === "patient") {
    return (
      <Page>
        <PageHeader
          title="Sign language"
          description="Signed lines play on your card and in Telegram. This screen does not watch you sign, and it does not guess what a sign means."
        />
        <Card as="section" aria-labelledby="sign-heading">
          <SectionHeader
            id="sign-heading"
            title="Your card speaks in sign"
            description="Open the card from the sign-in page. A signing figure plays each line, and the words are written underneath."
          />
          <p className="mt-4 text-sm text-ink-2">
            Clips stay off until a reviewer approves them. Until then the card says the sample is research, not a message about you.
          </p>
          <div className="mt-5">
            <ButtonLink href="/enter">Open the card</ButtonLink>
          </div>
        </Card>
      </Page>
    );
  }
  const allowed = ["admin", "program_manager", "ksl_reviewer"];
  if (!allowed.includes(user.role)) redirect("/escalations");

  let rows: ClipRow[] = [];
  let problem: string | null = null;
  try {
    rows = await api<ClipRow[]>("/ksl/clips");
  } catch (error) {
    problem = error instanceof ApiError ? error.message : "The clip list could not be loaded.";
  }

  const count = (status: string) => rows.filter((row) => row.status === status).length;
  const approved = count("approved");

  return (
    <Page>
      <PageHeader
        title="Sign language clips"
        description="Recorded sign language lines for the patient card and Telegram. A clip plays only after review, and lines still pending clinical review stay off for a pilot. This list stores labels, not anyone’s footage."
        meta={
          <>
            <Badge tone="outline" icon={<Camera aria-hidden="true" />}>
              Camera off, no sign recognition
            </Badge>
            <Badge tone="warn">Phrases pending clinical review</Badge>
          </>
        }
      />

      {problem ? <Notice tone="bad">{problem}</Notice> : null}

      {!problem && approved === 0 ? (
        <Notice tone="info" title="No approved clip in this build">
          Until one is approved, the patient card plays research samples instead, labelled on screen as research and
          not Kenyan Sign Language.
        </Notice>
      ) : null}

      {!problem ? (
        <StatBar
          label="Clips by status"
          items={[
            { label: "Waiting for review", value: count("uploaded"), tone: count("uploaded") ? "warn" : "default" },
            { label: "Approved", value: approved },
            { label: "Stale", value: count("stale"), tone: count("stale") ? "danger" : "default", hint: "Phrase changed after approval" },
            { label: "Retired", value: count("retired") },
          ]}
        />
      ) : null}

      <section aria-labelledby="clips-heading" className="space-y-3">
        <SectionHeader id="clips-heading" title="Clips" description="Every uploaded clip and where it stands." />
        {!problem && rows.length === 0 ? (
          <EmptyState icon={<Hand aria-hidden="true" />} title="No clips have been uploaded">
            That is the honest state of this build. A clip appears here once an editor uploads a recording of an
            approved phrase.
          </EmptyState>
        ) : null}
        {rows.length > 0 ? (
          <Table caption="Uploaded sign language clips">
            <THead>
              <Th>Phrase</Th>
              <Th>Label</Th>
              <Th>Status</Th>
              <Th>Pilot</Th>
            </THead>
            <tbody>
              {rows.map((row) => {
                const status = STATUS[row.status] ?? { label: row.status, tone: "neutral" as Tone };
                return (
                  <Tr key={row.id}>
                    <Td className="font-medium text-ink">{row.template_id}</Td>
                    <Td>
                      <Badge tone={labelTone(row.label)}>{row.label}</Badge>
                    </Td>
                    <Td>
                      <Badge tone={status.tone}>{status.label}</Badge>
                    </Td>
                    <Td>
                      {row.pilot_enabled ? (
                        <Badge tone="teal" icon={<CircleCheck aria-hidden="true" />}>
                          On for a pilot
                        </Badge>
                      ) : (
                        <span className="text-ink-2">Not for a pilot</span>
                      )}
                    </Td>
                  </Tr>
                );
              })}
            </tbody>
          </Table>
        ) : null}
      </section>

      <div className="grid items-start gap-6 lg:grid-cols-2">
        <Card as="section" aria-labelledby="steps-heading">
          <SectionHeader
            id="steps-heading"
            title="How a clip gets approved"
            description="The server enforces these checks in this order. If the phrase text changes later, the clip turns stale."
          />
          <ol className="mt-5 space-y-4">
            {STEPS.map(([title, line], index) => (
              <li key={title} className="flex gap-3">
                <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-deep text-[0.8125rem] font-semibold text-white">
                  {index + 1}
                </span>
                <span>
                  <span className="block font-medium text-ink">{title}</span>
                  <span className="text-sm text-ink-2">{line}</span>
                </span>
              </li>
            ))}
          </ol>
        </Card>

        <Card as="section" aria-labelledby="research-heading">
          <SectionHeader
            id="research-heading"
            title="Research samples"
            description="Public datasets used to test the player. None of them is a reviewed patient message."
          />
          <ul className="mt-5 space-y-3">
            <li className="rounded-xl border border-line p-4">
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium text-ink">American Sign Language sentences</p>
                <Badge tone="warn" icon={<FlaskConical aria-hidden="true" />}>
                  Research
                </Badge>
              </div>
              <p className="mt-1 text-sm text-ink-2">
                How2Sign sentences on the patient card, development servers only. CC BY-NC 4.0, credited on screen.
              </p>
            </li>
            <li className="rounded-xl border border-line p-4">
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium text-ink">Kenyan Sign Language word</p>
                <Badge tone="warn" icon={<FlaskConical aria-hidden="true" />}>
                  Research
                </Badge>
              </div>
              <p className="mt-1 text-sm text-ink-2">
                One word from the Maseno pose dataset. It loads only after someone verifies the licence.
              </p>
              <Link
                href="/dev/ksl-research"
                className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-teal-text hover:underline"
              >
                Open the research view
                <ArrowUpRight aria-hidden="true" className="size-4" />
              </Link>
            </li>
          </ul>
        </Card>
      </div>
    </Page>
  );
}
