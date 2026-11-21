import {
  Bandage,
  BriefcaseMedical,
  HeartPulse,
  Microscope,
  Pill,
  Stethoscope,
  Syringe,
  TestTube,
  Thermometer,
  type LucideIcon,
} from "lucide-react";
import type { CSSProperties } from "react";
import { cx } from "@/components/ui/cx";

type Floater = {
  icon: LucideIcon;
  top: string;
  left: string;
  size: number;
  /** how far it drifts sideways and up/down, and how much it turns, over one drift cycle */
  dx: number;
  dy: number;
  rot: number;
  /** seconds for one drift cycle and for one bounce */
  drift: number;
  bounce: number;
  delay: number;
  /** shown from tablet width up; phones get two items per panel so text stays clear */
  wide?: boolean;
};

// Positions are chosen to stay near the edges of each panel, away from the
// headline and the account list.
const DARK: Floater[] = [
  { icon: Stethoscope, top: "6%", left: "72%", size: 64, dx: -22, dy: 18, rot: 14, drift: 16, bounce: 3.4, delay: 0 },
  { icon: Syringe, top: "34%", left: "84%", size: 48, dx: -14, dy: -20, rot: -22, drift: 13, bounce: 2.8, delay: -4 },
  { icon: Pill, top: "58%", left: "6%", size: 40, dx: 18, dy: -14, rot: 30, drift: 11, bounce: 2.4, delay: -2, wide: true },
  { icon: HeartPulse, top: "80%", left: "78%", size: 52, dx: -18, dy: -12, rot: -10, drift: 15, bounce: 3.1, delay: -7, wide: true },
  { icon: Thermometer, top: "64%", left: "88%", size: 40, dx: 16, dy: -16, rot: 18, drift: 12, bounce: 2.6, delay: -5, wide: true },
  { icon: Bandage, top: "40%", left: "2%", size: 44, dx: 20, dy: 16, rot: -28, drift: 14, bounce: 3.6, delay: -9, wide: true },
  { icon: TestTube, top: "3%", left: "44%", size: 36, dx: 14, dy: 14, rot: 24, drift: 10, bounce: 2.2, delay: -3, wide: true },
];

const LIGHT: Floater[] = [
  { icon: BriefcaseMedical, top: "4%", left: "8%", size: 48, dx: 16, dy: 14, rot: -12, drift: 15, bounce: 3.2, delay: -1, wide: true },
  { icon: Syringe, top: "8%", left: "82%", size: 44, dx: -16, dy: 18, rot: 26, drift: 12, bounce: 2.7, delay: -6, wide: true },
  { icon: Microscope, top: "86%", left: "84%", size: 52, dx: -18, dy: -14, rot: 10, drift: 16, bounce: 3.5, delay: -3 },
  { icon: Pill, top: "90%", left: "10%", size: 38, dx: 18, dy: -12, rot: -30, drift: 11, bounce: 2.5, delay: -8 },
  { icon: Stethoscope, top: "48%", left: "92%", size: 46, dx: -14, dy: 16, rot: -16, drift: 14, bounce: 3, delay: -4, wide: true },
  { icon: HeartPulse, top: "52%", left: "1%", size: 40, dx: 14, dy: -16, rot: 12, drift: 13, bounce: 2.9, delay: -10, wide: true },
];

/**
 * Medical items that drift and bounce slowly behind a panel. Purely decorative:
 * hidden from screen readers, never clickable, and still for anyone who has asked
 * their device to reduce motion.
 */
export function MedicalFloaters({ tone }: { tone: "dark" | "light" }) {
  const items = tone === "dark" ? DARK : LIGHT;
  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
      {items.map((item, index) => {
        const Icon = item.icon;
        return (
          <span
            key={index}
            className={cx("cl-drift absolute", item.wide && "hidden md:block")}
            style={
              {
                top: item.top,
                left: item.left,
                "--dx": `${item.dx}px`,
                "--dy": `${item.dy}px`,
                "--rot": `${item.rot}deg`,
                animationDuration: `${item.drift}s`,
                animationDelay: `${item.delay}s`,
              } as CSSProperties
            }
          >
            <span
              className="cl-bounce block"
              style={{ animationDuration: `${item.bounce}s`, animationDelay: `${item.delay / 2}s` }}
            >
              <Icon
                size={item.size}
                strokeWidth={1.5}
                className={tone === "dark" ? "text-on-dark opacity-[0.13]" : "text-teal opacity-[0.12]"}
              />
            </span>
          </span>
        );
      })}
    </div>
  );
}
