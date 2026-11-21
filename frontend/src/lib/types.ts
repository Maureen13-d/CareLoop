// Response shapes shared by more than one page. Each mirrors an existing API response.

/** GET /navigator/tasks */
export type NavigatorTask = {
  id: number;
  case_id: number | null;
  patient_display_name?: string | null;
  patient_ref?: string | null;
  priority: string;
  title: string;
  summary: string;
  status?: string;
  source?: string;
  created_at?: string;
  contact_ref?: string | null;
};

/** GET /followup/worklist */
export type WorklistRow = {
  case_id: number;
  public_id: string;
  days_since_screening: number;
  state: string;
  reason: string;
  recommended_action: string;
};

export type Worklist = {
  synthetic: boolean;
  review: string;
  counts: { open: number; overdue: number; worse: number; unreached: number };
  rows: WorklistRow[];
};
