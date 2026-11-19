import { Nav } from "@/components/Nav";
import { ROLE_LABEL } from "@/lib/format";
import type { SessionUser } from "@/lib/session";
import { signOut } from "@/app/login/actions";

export function Shell({ user, children }: { user: SessionUser; children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <a href="#content" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-10 focus:rounded-full focus:bg-white focus:px-3 focus:py-2">
        Skip to content
      </a>
      <header className="border-b border-line bg-paper/90">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4">
          <div>
            <p className="font-serif text-xl leading-none">CareLoop</p>
            <p className="mt-1 text-xs text-ink-soft">Synthetic data. Not a clinical service.</p>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <p className="text-right">
              <span className="block font-medium">{user.display_name}</span>
              <span className="text-ink-soft">{ROLE_LABEL[user.role] ?? user.role}</span>
            </p>
            <form action={signOut}>
              <button className="rounded-full border border-line bg-paper-2 px-3 py-2 text-sm hover:border-lagoon">
                Sign out
              </button>
            </form>
          </div>
        </div>
      </header>
      <div className="mx-auto flex max-w-6xl flex-col md:flex-row md:gap-8 md:px-4 md:py-8">
        <Nav role={user.role} />
        <div id="content" className="min-w-0 flex-1">
          {children}
        </div>
      </div>
    </div>
  );
}
