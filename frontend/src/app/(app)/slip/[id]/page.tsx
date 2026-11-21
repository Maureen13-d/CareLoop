import { ShieldCheck } from "lucide-react";
import { redirect } from "next/navigation";
import { BrandMark, ButtonLink, Page, PageHeader } from "@/components/ui";
import { api } from "@/lib/api";
import { getSession } from "@/lib/session";
import { PrintButton } from "./PrintButton";

export const instant = false;

export default async function SlipPage({ params }: { params: Promise<{ id: string }> }) {
  const user = await getSession();
  if (!user) redirect("/login");
  const { id } = await params;
  const slip = await api<{ public_id: string; lines: string[]; qr_svg: string | null }>(
    `/followup/slip/${id}`,
  );

  return (
    <Page narrow>
      <div className="no-print">
        <PageHeader
          back={{ href: "/screen", label: "Issue another ID" }}
          title="The card to hand over"
          description="Give this to the person. It carries the ID and a QR code of the ID only. No result is printed on it."
          actions={
            <>
              <PrintButton />
              <ButtonLink href="/worklist">Who to chase</ButtonLink>
            </>
          }
        />
      </div>

      <article
        aria-label="ID card"
        className="mx-auto max-w-md overflow-hidden rounded-2xl border border-line bg-surface shadow-float print:shadow-none"
      >
        <div className="flex items-center justify-between bg-emerald px-6 py-4 text-white">
          <span className="inline-flex items-center gap-2 font-semibold">
            <BrandMark className="size-6" />
            CareLoop
          </span>
          <span className="text-sm text-on-dark-2">Synthetic</span>
        </div>
        <div className="space-y-5 px-6 py-6">
          <div>
            <p className="text-sm text-ink-2">Your ID</p>
            <p className="mt-1 text-[1.75rem] font-semibold tracking-[0.12em] text-ink">{slip.public_id}</p>
          </div>
          {slip.qr_svg ? (
            <div
              className="w-40 rounded-xl border border-line p-2 [&_svg]:h-auto [&_svg]:w-full"
              dangerouslySetInnerHTML={{ __html: slip.qr_svg }}
            />
          ) : (
            <p className="text-sm text-ink-2">The QR code encodes this ID only.</p>
          )}
          <div className="space-y-2 border-t border-line pt-5">
            {slip.lines.map((line) => (
              <p key={line} className="text-[1.0625rem] leading-snug text-ink">
                {line}
              </p>
            ))}
          </div>
          <p className="flex items-center gap-2 rounded-xl bg-mint px-3 py-2 text-sm text-teal-text">
            <ShieldCheck aria-hidden="true" className="size-4 shrink-0" />
            No result is printed on this card.
          </p>
        </div>
      </article>
    </Page>
  );
}
