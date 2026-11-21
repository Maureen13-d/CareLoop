export const STAGE_ORDER = [
  "SCREENING_FLAGGED",
  "PATIENT_ENGAGED",
  "BARRIERS_ASSESSED",
  "NAVIGATION_ACTIVE",
  "APPOINTMENT_BOOKED",
  "ARRIVAL_CONFIRMED",
  "HANDED_OFF",
] as const;

export const STAGE_SHORT: Record<string, string> = {
  SCREENING_FLAGGED: "Invited",
  PATIENT_ENGAGED: "Joined",
  BARRIERS_ASSESSED: "Worries heard",
  NAVIGATION_ACTIVE: "Navigating",
  APPOINTMENT_BOOKED: "Visit booked",
  ARRIVAL_CONFIRMED: "Arrived",
  HANDED_OFF: "With the hospital",
  CLOSED: "Closed",
  PATIENT_DECLINED: "Chose to stop",
  LOST_TO_FOLLOW_UP: "Closed by a person",
  screened: "Screened",
  contacted: "Contacted",
  joined: "Joined",
  barrier_identified: "Barrier named",
  enrolled: "Enrolled",
  home_screened: "Home check",
  risk_flagged: "Needs a person",
  navigating: "Navigating",
  visit_booked: "Visit booked",
  arrived: "Arrived",
  with_hospital: "With the hospital",
  delivery_planned: "Plan recorded",
  postnatal_watch: "Postnatal watch",
  closed: "Closed",
  chose_to_stop: "Chose to stop",
  closed_by_person: "Closed by a person",
};

export const ROLE_LABEL: Record<string, string> = {
  navigator: "Navigator",
  clinician: "Clinician",
  counsellor: "Counsellor",
  program_manager: "Program manager",
  admin: "Admin",
  patient: "Patient",
  chw: "Community health promoter",
};

export function stageShort(state: string): string {
  return STAGE_SHORT[state] ?? state.replaceAll("_", " ").toLowerCase();
}

export function formatWhen(iso: string): string {
  return new Date(iso).toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  });
}

export const FACILITIES = [
  {
    name: "Demo Health Centre, Kisumu",
    note: "Weekday mornings. A navigator can ask about the fee before you travel.",
  },
  {
    name: "Demo Clinic, Westlands",
    note: "Navigation desk on site. Synthetic — not a real clinic.",
  },
  {
    name: "Demo County Hospital",
    note: "For a closer look after arrival. The hospital’s own team takes over.",
  },
];
