import { redirect } from "next/navigation";
import { Badge, Page, PageHeader } from "@/components/ui";
import { DEMO_CARD_ID } from "@/lib/demoCard";
import { getSession } from "@/lib/session";

export const instant = false;

const BOT_HANDLE = "@LoopieCareBot";
const BOT_URL = "https://t.me/LoopieCareBot";

export default async function TelegramPage() {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role !== "patient") redirect("/escalations");
  return (
    <Page narrow>
      <PageHeader
        title="Telegram"
        description="Chat with the follow-up guide on the real Telegram bot. Scan the code below, or open the link on this phone."
        meta={<Badge tone="outline">Live bot</Badge>}
      />
      <section
        aria-labelledby="telegram-qr-heading"
        className="mx-auto flex w-full max-w-md flex-col items-center text-center"
      >
        <h2 id="telegram-qr-heading" className="sr-only">
          Scan to open {BOT_HANDLE}
        </h2>
        <a
          href={BOT_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-2xl focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-teal"
        >
          <img
            src="/loopiecarebot-qr.png"
            alt={`QR code for ${BOT_HANDLE} on Telegram`}
            width={862}
            height={1024}
            className="mx-auto w-full max-w-sm"
          />
        </a>
        <div className="mt-6 space-y-3 px-2">
          <p className="text-[1.0625rem] leading-relaxed text-ink">
            Scan this code with your phone camera. It opens a chat with{" "}
            <a
              href={BOT_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-teal-text underline-offset-2 hover:underline"
            >
              {BOT_HANDLE}
            </a>{" "}
            on Telegram — the CareLoop follow-up guide.
          </p>
          <p className="text-[0.9375rem] leading-relaxed text-ink-2">
            When the guide asks for the ID on your card, type{" "}
            <span className="font-medium text-ink">{DEMO_CARD_ID}</span>. That is the same ID as the
            sign-language card.
          </p>
        </div>
      </section>
    </Page>
  );
}
