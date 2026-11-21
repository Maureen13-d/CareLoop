# Frontend design system

How the CareLoop web app looks and why. Read this before adding a page or a component.

## Direction

Deep teal and emerald on a cool mint canvas, with white working surfaces. The dark emerald is kept for the parts that frame the work: the sidebar, the dashboard hero, the login brand panel, and simulated devices. Everything people read and act on sits on white. The look borrows the calm, rounded feel of modern clinical sites, but CareLoop is a working tool, so there is no marketing photography. The one illustration, on the sign-in page, is the pathway itself drawn as a loop.

## Colour tokens (`src/app/globals.css`)

| Token | Value | Use |
|---|---|---|
| `canvas` | `#F5F8F7` | Page background |
| `surface` | `#FFFFFF` | Cards, tables, forms |
| `mint` | `#E7F5F1` | Selected and supporting surfaces |
| `mint-strong` | `#CFEAE2` | Borders on mint |
| `ink` | `#183B38` | Main text |
| `ink-2` | `#5B6F6B` | Secondary text (5.3:1 on white) |
| `ink-3` | `#718581` | Icons and decoration only (3.9:1, not for text) |
| `line` | `#DFEAE6` | Dividers and card borders |
| `control` | `#7D9893` | Form control borders (3.1:1 on white) |
| `deep` | `#075B55` | Primary buttons (8:1 with white text) |
| `emerald` | `#064B45` | Sidebar, hero, brand panel |
| `teal` | `#0F8B80` | Bars, rings, focus outline, accents |
| `teal-text` | `#0B7469` | Teal used as text (5.6:1 on white) |
| `danger` / `danger-bg` | `#B42318` / `#FDECEA` | Urgent, escalated, errors |
| `warn` / `warn-bg` | `#9A3F07` / `#FEF0DC` | Overdue, synthetic-data notes |

The brief's primary teal `#0F8B80` and grey `#718581` fail WCAG AA as small text (4.2:1 and 3.9:1). They are kept for fills, icons and focus rings, and darker versions are used for text.

Status is never shown by colour alone: every badge carries a word.

## Type

One family, Outfit (variable, SIL Open Font License), self-hosted from `src/app/fonts/` through `next/font/local`. The build and the running app make no Google Fonts request. Hierarchy comes from size and weight:

| Role | Size |
|---|---|
| Dashboard and sign-in headline | 40–44px, semibold |
| Page title (`PageHeader`) | 28–32px, semibold |
| Section title (`SectionHeader`) | 18px, semibold |
| Body | 15–16px |
| Meta, hints, table headers | 13px |

Numbers in stats use tabular figures. Labels are sentence case. Upper-case strings from the API (such as `PENDING CLINICAL REVIEW`) are converted to sentence case for display.

## Shape and depth

- Buttons and filters are pills (`rounded-full`).
- Form controls use 12px radius (`rounded-xl`), and cards 16px (`rounded-2xl`).
- The dashboard hero uses 28px.
- There are two shadows. `shadow-raised` is for cards and tables. `shadow-float` is for menus, the phone handset and the ID card.

## Layout

- **Signed-in workspace:** a 272px dark sidebar on large screens, with nav grouped into *Work*, *Patient channels* and *Oversight*, and the user and sign-out at the foot. Below 1024px it becomes a top bar with a menu that closes itself after you pick a page.
- **Page width:** every page uses `<Page>` (max width 1152px, or 768px with `narrow`) and starts with `<PageHeader>`.
- **Tables:** they scroll sideways inside their own frame, never the page. The main lists (cases, follow-up queue, audit) switch to cards on phones.

## Components (`src/components/ui/`)

Import from `@/components/ui`. Client components are imported from their own files.

| Component | Purpose |
|---|---|
| `Button`, `ButtonLink`, `buttonClasses` | Variants: `primary`, `secondary`, `ghost`, `danger`, `on-dark`, `on-dark-outline`. Sizes: `sm`, `md`, `lg` |
| `SubmitButton` (client) | Form submit with a pending state; cannot be pressed twice |
| `Field`, `Input`, `Select`, `Textarea`, `CheckField`, `FormSection` | Labelled controls with hints |
| `Card`, `SectionHeader`, `KeyValue` | Surfaces and section headings with an optional action |
| `PageHeader`, `Page` | Page title, description, back link, badges, actions, width |
| `Badge` | Tones: `neutral`, `teal`, `solid`, `warn`, `danger`, `outline` |
| `StatBar`, `MetricCard`, `NoValue` | Headline numbers. `StatBar` is one surface with dividers, not a row of cards |
| `Table`, `THead`, `Th`, `Tr`, `Td` | Data tables with a screen-reader caption |
| `FilterTabs` | Link-based filters (each view has a URL) |
| `Timeline`, `TimelineItem` | Case and outreach history |
| `JourneyStepper`, `JourneyMeter` | Pathway progress; the stepper collapses to a bar on phones |
| `ProgressRing`, `Meter` | Shares and counts on one scale |
| `Notice`, `Banner` | Action feedback (errors are `role="alert"`) and the synthetic-data reminder |
| `EmptyState`, `Skeleton` | Empty lists and loading placeholders |
| `ErrorPanel` (client) | Body of an `error.tsx` boundary |
| `BrandMark`, `Wordmark`, `Avatar` | Brand and initials |

Shared app components in `src/components/`:

| Component | Purpose |
|---|---|
| `Shell` | The signed-in layout |
| `Nav` | Sidebar and phone menu; role lists as before |
| `TaskItem` | An open navigator task with "Mark done" |
| `PathwayFunnel` | People per step |
| `JourneyLoop` | The sign-in illustration |
| `OutreachKind` | Outreach labels and badges |

`src/lib/status.ts` maps API statuses to badge tones and labels. It holds display rules only, no business rules. Response types shared by several pages are in `src/lib/types.ts`.

## Rules to keep

- Only links a role may open appear in its navigation. The pages still check the role on the server.
- Patient-facing text never names a finding or a condition. The SMS, USSD and Telegram simulators are labelled as simulated.
- The assistant never appears to diagnose. Human handoff has its own visible treatment, and approved sources are shown with their review status.
- Lost to follow-up, closing a case and confirming an arrival are presented as human decisions.
- Every interactive element has a visible focus outline, a label, and a tap target of at least 36px (44px for primary actions).
- Motion is limited to the pending spinner, the chat typing dots and the guide's speaking indicator. `prefers-reduced-motion` turns it off.
