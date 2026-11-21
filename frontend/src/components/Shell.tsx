import { FlaskConical, LogOut } from "lucide-react";
import Link from "next/link";
import { signOut } from "@/app/login/actions";
import { MobileMenu, SidebarNav } from "@/components/Nav";
import { Avatar, Wordmark } from "@/components/ui";
import { cx } from "@/components/ui/cx";
import { ROLE_LABEL } from "@/lib/format";
import type { SessionUser } from "@/lib/session";

function SignOut({ onDark }: { onDark: boolean }) {
  return (
    <form action={signOut}>
      <button
        type="submit"
        className={cx(
          "inline-flex min-h-9 items-center gap-2 rounded-full px-3 text-sm font-medium",
          onDark ? "text-on-dark hover:bg-white/10" : "text-teal-text hover:bg-mint",
        )}
      >
        <LogOut aria-hidden="true" className="size-4" />
        Sign out
      </button>
    </form>
  );
}

function Who({ user, onDark }: { user: SessionUser; onDark: boolean }) {
  return (
    <div className="flex min-w-0 items-center gap-3">
      <Avatar name={user.display_name} className={onDark ? "bg-white/12 text-white" : undefined} />
      <div className="min-w-0">
        <p className={cx("truncate text-sm font-medium", onDark ? "text-white" : "text-ink")}>{user.display_name}</p>
        <p className={cx("truncate text-[0.8125rem]", onDark ? "text-on-dark-2" : "text-ink-2")}>
          {ROLE_LABEL[user.role] ?? user.role}
        </p>
      </div>
    </div>
  );
}

function DemoNote({ onDark }: { onDark: boolean }) {
  return (
    <p className={cx("flex items-center gap-2 text-[0.8125rem]", onDark ? "text-on-dark-2" : "text-ink-2")}>
      <FlaskConical aria-hidden="true" className="size-4 shrink-0" />
      Synthetic data. Not a clinical service.
    </p>
  );
}

export function Shell({ user, children }: { user: SessionUser; children: React.ReactNode }) {
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[17rem_1fr] print:block">
      <a
        href="#content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-full focus:bg-surface focus:px-4 focus:py-2 focus:text-ink focus:shadow-float"
      >
        Skip to content
      </a>

      {/* desktop sidebar */}
      <aside className="no-print sticky top-0 hidden h-screen flex-col bg-emerald px-4 py-6 lg:flex">
        <Link href="/" className="rounded-xl px-2 text-white">
          <Wordmark tone="light" />
        </Link>
        <div className="mt-2 px-2">
          <DemoNote onDark />
        </div>
        <div className="mt-8 flex-1 overflow-y-auto pr-1">
          <SidebarNav role={user.role} />
        </div>
        <div className="mt-6 space-y-3 border-t border-white/10 px-2 pt-5">
          <Who user={user} onDark />
          <SignOut onDark />
        </div>
      </aside>

      {/* phone and tablet top bar */}
      <header className="no-print sticky top-0 z-20 bg-emerald lg:hidden">
        <div className="relative flex h-16 items-center justify-between px-4">
          <Link href="/" className="rounded-xl text-white">
            <Wordmark tone="light" />
          </Link>
          <MobileMenu
            role={user.role}
            footer={
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <Who user={user} onDark={false} />
                  <SignOut onDark={false} />
                </div>
                <DemoNote onDark={false} />
              </div>
            }
          />
        </div>
      </header>

      <div className="min-w-0">{children}</div>
    </div>
  );
}
