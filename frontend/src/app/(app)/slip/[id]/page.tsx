import { redirect } from "next/navigation";
import { api } from "@/lib/api";
import { getSession } from "@/lib/session";

export const instant = false;

export default async function SlipPage({ params }: { params: Promise<{ id: string }> }) {
  const user = await getSession();
  if (!user) redirect("/login");
  const { id } = await params;
  const slip = await api<{ public_id: string; lines: string[]; qr_svg: string | null }>(
    `/followup/slip/${id}`,
  );

  return (
    <main className="mx-auto max-w-md space-y-4 bg-white px-6 py-8 print:shadow-none">
      <p className="text-sm text-lagoon">SYNTHETIC</p>
      <h1 className="text-3xl tracking-widest">{slip.public_id}</h1>
      {slip.qr_svg ? (
        <div className="w-40" dangerouslySetInnerHTML={{ __html: slip.qr_svg }} />
      ) : (
        <p className="text-sm text-ink-soft">QR encodes this ID only.</p>
      )}
      {slip.lines.map((line) => (
        <p key={line} className="text-lg">
          {line}
        </p>
      ))}
      <p className="text-sm text-ink-soft">No result is printed on this card.</p>
    </main>
  );
}
