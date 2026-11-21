"use client";

import {
  CircleExclamationPoint,
  FlaskConical,
  HeartHandshake,
  Languages,
  LoaderCircle,
  Pause,
  Play,
  RotateCcw,
  Snail,
} from "lucide-react";
import { useCallback, useState } from "react";
import { Wordmark } from "@/components/ui/brand";
import { cx } from "@/components/ui/cx";
import { AslSample, type SignedLine } from "@/ksl/AslSample";

export type SignAnswer = { id: string; label: string };

function prefersReducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

const control =
  "inline-flex min-h-10 items-center gap-1.5 rounded-full border border-line bg-surface px-3.5 text-sm font-medium text-ink " +
  "transition-colors hover:border-teal hover:bg-mint aria-pressed:border-teal aria-pressed:bg-mint aria-pressed:text-teal-text " +
  "[&_svg]:size-4";

/**
 * The patient card in sign language: a signing figure, the line it signs as text,
 * the guide's reply after every answer, and taps to answer.
 *
 * The clips are research samples, not reviewed patient messages, so the screen
 * always says so and credits the source.
 */
export function SignSession({
  step,
  total,
  answers,
  reply,
  danger,
  busy,
  error,
  onLines,
  onAnswer,
  onLeave,
}: {
  step: number;
  total: number;
  answers: SignAnswer[];
  /** the guide's last reply, as text; always shown so no answer goes unacknowledged */
  reply: string | null;
  danger: boolean;
  busy: boolean;
  error: string;
  onLines: (ids: string[]) => void;
  onAnswer: (id: string) => void;
  onLeave: () => void;
}) {
  const [line, setLine] = useState<SignedLine | null>(null);
  const [problem, setProblem] = useState("");
  // Anyone who asked their device for less motion starts on a still figure and presses play.
  // This screen only appears after a tap, so it never renders on the server.
  const [paused, setPaused] = useState(prefersReducedMotion);
  const [slow, setSlow] = useState(false);
  const [replay, setReplay] = useState(0);

  const showLine = useCallback((next: SignedLine | null) => setLine(next), []);
  const showProblem = useCallback((message: string) => setProblem(message), []);

  return (
    <div className="flex min-h-dvh flex-col bg-canvas text-ink">
      <header className="no-print bg-emerald">
        <div className="mx-auto flex h-16 max-w-3xl items-center justify-between gap-3 px-4">
          <Wordmark tone="light" />
          <button
            type="button"
            onClick={onLeave}
            className="inline-flex min-h-10 items-center gap-2 rounded-full border border-white/30 px-4 text-sm font-medium text-white hover:bg-white/10"
          >
            <Languages aria-hidden="true" className="size-4" />
            Use English instead
          </button>
        </div>
      </header>

      <main id="content" className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-4 px-4 py-4 sm:py-6">
        <p className="flex items-start gap-2.5 rounded-xl border border-warn/25 bg-warn-bg px-4 py-2.5 text-sm text-warn">
          <FlaskConical aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
          <span>
            <span className="font-semibold">Research sample in American Sign Language.</span> Not Kenyan Sign Language,
            not reviewed, and not a message written for you. The words under the figure say what it signs.
          </span>
        </p>

        {problem ? (
          <section className="flex flex-1 flex-col items-center justify-center rounded-2xl border border-line bg-surface p-8 text-center shadow-raised">
            <p className="text-lg font-semibold">Signed lines are not available here</p>
            <p className="mt-2 max-w-sm text-[0.9375rem] text-ink-2">
              This server does not have the sign language clips. You can carry on in English with captions; nothing
              you have answered is lost.
            </p>
            <button
              type="button"
              onClick={onLeave}
              className="mt-5 inline-flex min-h-12 items-center rounded-full bg-deep px-6 font-medium text-white hover:bg-emerald"
            >
              Continue in English
            </button>
          </section>
        ) : (
          <section aria-label="Signing figure" className="overflow-hidden rounded-2xl border border-line bg-surface shadow-raised">
            <div className="relative h-[46dvh] min-h-64 sm:h-[52dvh]">
              <AslSample
                step={step}
                onLines={onLines}
                onLine={showLine}
                onProblem={showProblem}
                paused={paused}
                speed={slow ? 0.75 : 1}
                replay={replay}
              />
              <span className="absolute top-3 left-3 rounded-full bg-surface/90 px-2.5 py-0.5 text-[0.8125rem] font-medium text-ink-2 shadow-raised">
                Line {Math.min(step + 1, total)} of {total}
              </span>
            </div>
            <div className="border-t border-line px-4 py-3 sm:px-5">
              <p aria-live="polite" className="text-center text-xl font-semibold leading-snug sm:text-2xl">
                {line ? line.sentence : <span className="text-ink-3">Loading the line…</span>}
              </p>
              <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
                <button
                  type="button"
                  className={control}
                  aria-pressed={paused}
                  onClick={() => setPaused((value) => !value)}
                >
                  {paused ? <Play aria-hidden="true" /> : <Pause aria-hidden="true" />}
                  {paused ? "Play" : "Pause"}
                </button>
                <button
                  type="button"
                  className={control}
                  onClick={() => {
                    setReplay((value) => value + 1);
                    setPaused(false);
                  }}
                >
                  <RotateCcw aria-hidden="true" />
                  Again
                </button>
                <button type="button" className={control} aria-pressed={slow} onClick={() => setSlow((value) => !value)}>
                  <Snail aria-hidden="true" />
                  Slower
                </button>
              </div>
            </div>
          </section>
        )}

        {reply ? (
          danger ? (
            <section
              role="alert"
              className="flex gap-3 rounded-2xl border-2 border-danger bg-danger-bg px-4 py-4 text-danger sm:px-5"
            >
              <CircleExclamationPoint aria-hidden="true" className="mt-0.5 size-6 shrink-0" />
              <div>
                <p className="text-sm font-medium">The guide says</p>
                <p className="mt-1 text-xl font-semibold leading-snug">{reply}</p>
              </div>
            </section>
          ) : (
            <section aria-live="polite" className="flex gap-3 rounded-2xl border border-mint-strong bg-mint px-4 py-3 sm:px-5">
              <HeartHandshake aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-teal-text" />
              <div>
                <p className="text-sm font-medium text-teal-text">The guide says</p>
                <p className="mt-0.5 text-[1.0625rem] leading-snug text-ink">{reply}</p>
              </div>
            </section>
          )
        ) : null}

        {!problem ? (
          <section aria-labelledby="answer-heading" className="mt-auto">
            <h2 id="answer-heading" className="mb-2 text-base">
              Your answer
            </h2>
            <div className="grid grid-cols-2 gap-2 pb-[env(safe-area-inset-bottom)]">
              {answers.map((item, index) => (
                <button
                  key={item.id}
                  type="button"
                  disabled={busy}
                  onClick={() => onAnswer(item.id)}
                  className={cx(
                    "min-h-14 rounded-2xl bg-deep px-3 text-[1.0625rem] font-medium text-white transition-colors hover:bg-emerald disabled:opacity-60",
                    index === answers.length - 1 && answers.length % 2 === 1 && "col-span-2",
                  )}
                >
                  {item.label}
                </button>
              ))}
            </div>
            {busy ? (
              <p className="mt-2 inline-flex items-center gap-2 text-sm text-ink-2">
                <LoaderCircle aria-hidden="true" className="size-4 animate-spin" />
                Sending your answer
              </p>
            ) : null}
            {error ? (
              <p role="alert" className="mt-2 text-sm text-danger">
                {error}
              </p>
            ) : null}
            <p className="mt-3 text-[0.8125rem] text-ink-2">
              Answers are taps. The camera stays off. If you feel worse, go to the nearest clinic.
            </p>
          </section>
        ) : null}

        <details className="rounded-xl border border-line bg-surface px-4 py-3 text-sm text-ink-2">
          <summary className="cursor-pointer font-medium text-ink">About these clips</summary>
          <p className="mt-2">{line?.label || "ASL research: How2Sign sentence. Not a patient message. Not reviewed."}</p>
          {line?.citation ? <p className="mt-2">{line.citation}</p> : null}
        </details>
      </main>
    </div>
  );
}
