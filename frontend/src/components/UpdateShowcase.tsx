"use client";

import { FileText, Play } from "lucide-react";
import { useEffectEvent, useState, type CSSProperties, type PointerEvent } from "react";
import { cx } from "@/components/ui";

const SLIDES_HREF = "/CareLoop_Future_Health_Submission_v3.pdf";
const VIDEO_HREF = "https://youtu.be/-1ubm_kUkTM";

function ShowcaseLink({
  href,
  title,
  hint,
  icon,
  tone,
}: {
  href: string;
  title: string;
  hint: string;
  icon: "slides" | "video";
  tone: "solid" | "outline";
}) {
  const [tilt, setTilt] = useState({ x: 0, y: 0, mx: 50, my: 50 });
  const [active, setActive] = useState(false);
  const Icon = icon === "slides" ? FileText : Play;

  const onPointerMove = useEffectEvent((event: PointerEvent<HTMLAnchorElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    const px = (event.clientX - box.left) / box.width;
    const py = (event.clientY - box.top) / box.height;
    setTilt({
      x: (py - 0.5) * -8,
      y: (px - 0.5) * 10,
      mx: px * 100,
      my: py * 100,
    });
  });

  const onPointerEnter = useEffectEvent(() => setActive(true));
  const onPointerLeave = useEffectEvent(() => {
    setActive(false);
    setTilt({ x: 0, y: 0, mx: 50, my: 50 });
  });

  const style = {
    transform: active
      ? `perspective(700px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg) translateY(-2px) scale(1.02)`
      : "perspective(700px) rotateX(0deg) rotateY(0deg) translateY(0) scale(1)",
    ["--mx" as string]: `${tilt.mx}%`,
    ["--my" as string]: `${tilt.my}%`,
  } as CSSProperties;

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      onPointerMove={onPointerMove}
      onPointerEnter={onPointerEnter}
      onPointerLeave={onPointerLeave}
      style={style}
      className={cx(
        "group relative flex min-h-[5.25rem] flex-1 items-center gap-3.5 overflow-hidden rounded-2xl px-4 py-3.5 text-left transition-[transform,box-shadow,background-color,border-color] duration-200 ease-out will-change-transform",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-teal",
        tone === "solid"
          ? "bg-on-dark text-emerald shadow-float hover:bg-white"
          : "border border-white/35 bg-white/8 text-white backdrop-blur-[2px] hover:border-white/55 hover:bg-white/14",
      )}
    >
      <span
        aria-hidden="true"
        className={cx(
          "pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300",
          active && "opacity-100",
          tone === "solid"
            ? "bg-[radial-gradient(circle_at_var(--mx)_var(--my),rgb(15_139_128/0.2),transparent_55%)]"
            : "bg-[radial-gradient(circle_at_var(--mx)_var(--my),rgb(231_245_241/0.2),transparent_55%)]",
        )}
      />
      <span
        aria-hidden="true"
        className={cx(
          "relative flex size-11 shrink-0 items-center justify-center rounded-full transition-transform duration-300",
          tone === "solid" ? "bg-emerald text-on-dark" : "bg-white/15 text-white",
          active && (icon === "video" ? "scale-110" : "-rotate-6 scale-110"),
        )}
      >
        <Icon className={cx("size-5", icon === "video" && "translate-x-px")} />
      </span>
      <span className="relative min-w-0">
        <span className="block text-[0.9875rem] font-semibold leading-snug">{title}</span>
        <span
          className={cx(
            "mt-0.5 block text-[0.8125rem] leading-snug",
            tone === "solid" ? "text-emerald/75" : "text-on-dark-2",
          )}
        >
          {hint}
        </span>
      </span>
      <span
        aria-hidden="true"
        className={cx(
          "relative ml-auto text-lg transition-transform duration-300",
          active ? "translate-x-1" : "translate-x-0",
          tone === "solid" ? "text-emerald/55" : "text-white/55",
        )}
      >
        →
      </span>
    </a>
  );
}

/** Two update CTAs for the sign-in landing: slides PDF and demo video. */
export function UpdateShowcase({ className }: { className?: string }) {
  return (
    <div className={cx("w-full max-w-xl", className)}>
      <p className="text-sm font-medium text-on-dark-2">What&apos;s new for this round</p>
      <div className="mt-3 flex flex-col gap-3 sm:flex-row">
        <ShowcaseLink
          href={SLIDES_HREF}
          title="Read the update slides"
          hint="Open the Future Health deck as a PDF"
          icon="slides"
          tone="solid"
        />
        <ShowcaseLink
          href={VIDEO_HREF}
          title="See the updated video"
          hint="Watch the walkthrough on YouTube"
          icon="video"
          tone="outline"
        />
      </div>
    </div>
  );
}
