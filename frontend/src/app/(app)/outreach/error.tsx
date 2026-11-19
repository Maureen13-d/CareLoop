"use client";

export default function OutreachError({ reset }: { reset: () => void }) {
  return (
    <main className="mx-auto max-w-5xl space-y-4 p-8">
      <h1 className="text-2xl font-semibold">Outreach unavailable</h1>
      <p role="alert">
        Could not reach the CareLoop API. Check that the backend is running, then try again.
      </p>
      <button
        type="button"
        onClick={reset}
        className="rounded-md border border-black/20 px-4 py-2 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-700 dark:border-white/30"
      >
        Try again
      </button>
    </main>
  );
}
