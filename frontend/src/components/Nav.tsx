"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Today", roles: ["navigator", "clinician", "counsellor", "program_manager", "admin"] },
  { href: "/desk", label: "Cases", roles: ["navigator", "clinician"] },
  { href: "/intake", label: "New finding", roles: ["clinician"] },
  { href: "/phone", label: "Phone", roles: ["navigator", "clinician", "counsellor", "program_manager", "admin", "patient"] },
  { href: "/chat", label: "Chat", roles: ["navigator", "clinician", "counsellor", "admin", "patient"] },
  { href: "/outreach", label: "Follow-up", roles: ["navigator", "clinician", "program_manager", "admin"] },
  { href: "/audit", label: "Audit", roles: ["program_manager", "admin"] },
];

function Item({ href, label, current }: { href: string; label: string; current: boolean }) {
  return (
    <Link
      href={href}
      aria-current={current ? "page" : undefined}
      className={`block rounded-full px-3 py-2 text-sm ${
        current ? "bg-lagoon text-white" : "text-ink hover:bg-white"
      }`}
    >
      {label}
    </Link>
  );
}

export function Nav({ role }: { role: string }) {
  const path = usePathname();
  const links = LINKS.filter((link) => link.roles.includes(role));
  const current = (href: string) => (href === "/" ? path === "/" : path === href || path.startsWith(`${href}/`));

  return (
    <>
      <nav aria-label="Primary" className="flex gap-1 overflow-x-auto px-4 pb-4 md:hidden">
        {links.map((link) => (
          <Item key={link.href} {...link} current={current(link.href)} />
        ))}
      </nav>
      <nav aria-label="Primary" className="sticky top-6 hidden w-48 shrink-0 md:block">
        <ul className="space-y-1">
          {links.map((link) => (
            <li key={link.href}>
              <Item {...link} current={current(link.href)} />
            </li>
          ))}
        </ul>
      </nav>
    </>
  );
}
