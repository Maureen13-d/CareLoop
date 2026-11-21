"use client";

import {
  Hand,
  Activity,
  BellRing,
  DoorOpen,
  FilePlus,
  FolderOpen,
  HeartHandshake,
  House,
  IdCard,
  ListChecks,
  Menu,
  MessagesSquare,
  Mic,
  ScrollText,
  Send,
  Smartphone,
  X,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cx } from "@/components/ui/cx";

type NavLink = { href: string; label: string; icon: LucideIcon; roles: string[] };

// A link only appears for roles the page itself admits. The pages still check the role.
const STAFF = ["navigator", "clinician", "counsellor", "program_manager", "admin", "chw", "ksl_reviewer"];

const GROUPS: { title: string; links: NavLink[] }[] = [
  {
    title: "Work",
    links: [
      { href: "/", label: "Today", icon: House, roles: ["navigator", "clinician", "counsellor", "program_manager", "admin", "chw"] },
      { href: "/escalations", label: "Escalated cases", icon: HeartHandshake, roles: STAFF },
      { href: "/desk", label: "Cases", icon: FolderOpen, roles: ["navigator", "clinician"] },
      { href: "/worklist", label: "Who to chase", icon: ListChecks, roles: ["chw", "navigator", "clinician", "admin", "program_manager"] },
      { href: "/facility", label: "Arrivals", icon: DoorOpen, roles: ["clinician", "navigator", "program_manager", "admin"] },
      { href: "/intake", label: "Open a case", icon: FilePlus, roles: ["clinician"] },
      { href: "/screen", label: "Issue an ID card", icon: IdCard, roles: ["clinician"] },
    ],
  },
  {
    title: "Patient channels",
    links: [
      { href: "/chat", label: "Support chat", icon: MessagesSquare, roles: ["patient"] },
      { href: "/phone", label: "Basic phone", icon: Smartphone, roles: ["patient"] },
      { href: "/telegram", label: "Telegram", icon: Send, roles: ["patient"] },
      { href: "/voice", label: "Voice", icon: Mic, roles: ["patient"] },
      { href: "/hub", label: "Cuff hub", icon: Activity, roles: ["patient"] },
      { href: "/ksl", label: "Sign language", icon: Hand, roles: ["patient"] },
    ],
  },
  {
    title: "Oversight",
    links: [
      { href: "/outreach", label: "Follow-up ladder", icon: BellRing, roles: ["navigator", "clinician", "program_manager", "admin"] },
      { href: "/ksl", label: "Clip review", icon: Hand, roles: ["admin", "program_manager", "ksl_reviewer"] },
      { href: "/audit", label: "Audit trail", icon: ScrollText, roles: ["program_manager", "admin"] },
    ],
  },
];

function useGroups(role: string) {
  return GROUPS.map((group) => ({ ...group, links: group.links.filter((link) => link.roles.includes(role)) })).filter(
    (group) => group.links.length > 0,
  );
}

function isCurrent(path: string, href: string) {
  if (href === "/") return path === "/";
  // the outreach case page lives under /cases but belongs to the follow-up ladder
  if (href === "/outreach" && path.startsWith("/cases/")) return true;
  // the CHW home-check page belongs to Today
  return path === href || path.startsWith(`${href}/`);
}

function Links({ role, onDark }: { role: string; onDark: boolean }) {
  const path = usePathname();
  const groups = useGroups(role);
  const showTitles = groups.length > 1;
  return (
    <div className="space-y-6">
      {groups.map((group) => (
        <div key={group.title}>
          {showTitles ? (
            <p className={cx("mb-1.5 px-3 text-[0.75rem] font-medium", onDark ? "text-on-dark-2" : "text-ink-2")}>
              {group.title}
            </p>
          ) : null}
          <ul className="space-y-0.5">
            {group.links.map(({ href, label, icon: Icon }) => {
              const current = isCurrent(path, href);
              return (
                <li key={href}>
                  <Link
                    href={href}
                    aria-current={current ? "page" : undefined}
                    className={cx(
                      "flex min-h-10 items-center gap-3 rounded-xl px-3 text-[0.9375rem] transition-colors",
                      onDark
                        ? current
                          ? "bg-white/12 font-medium text-white"
                          : "text-on-dark/85 hover:bg-white/8 hover:text-white"
                        : current
                          ? "bg-mint font-medium text-emerald"
                          : "text-ink hover:bg-mint/60",
                    )}
                  >
                    <Icon
                      aria-hidden="true"
                      className={cx("size-[1.125rem] shrink-0", onDark ? (current ? "text-teal" : "text-on-dark-2") : "text-teal-text")}
                      strokeWidth={current ? 2.25 : 1.75}
                    />
                    {label}
                    {current && onDark ? <span aria-hidden="true" className="ml-auto size-1.5 rounded-full bg-teal" /> : null}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}

/** Links for the desktop sidebar. */
export function SidebarNav({ role }: { role: string }) {
  return (
    <nav aria-label="Primary" className="on-dark">
      <Links role={role} onDark />
    </nav>
  );
}

/**
 * The phone menu: a disclosure that closes itself after you pick a page
 * (it is re-mounted on every route change).
 */
export function MobileMenu({ role, footer }: { role: string; footer: React.ReactNode }) {
  const path = usePathname();
  return (
    <details key={path} className="group lg:hidden">
      <summary
        className="flex size-10 cursor-pointer list-none items-center justify-center rounded-full text-white hover:bg-white/10 [&::-webkit-details-marker]:hidden"
        aria-label="Menu"
      >
        <Menu aria-hidden="true" className="size-5 group-open:hidden" />
        <X aria-hidden="true" className="hidden size-5 group-open:block" />
      </summary>
      <div className="absolute inset-x-0 top-full z-30 max-h-[calc(100dvh-4rem)] overflow-y-auto border-b border-line bg-surface px-4 pt-4 pb-6 shadow-float">
        <nav aria-label="Primary">
          <Links role={role} onDark={false} />
        </nav>
        <div className="mt-6 border-t border-line pt-4">{footer}</div>
      </div>
    </details>
  );
}
