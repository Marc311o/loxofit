export type PlanStatus = "draft" | "active" | "archived";

export type VolumeZone = "below_mev" | "mev_mav" | "mav_mrv" | "above_mrv";

// ---------------------------------------------------------------------------
// Read
// ---------------------------------------------------------------------------

export type PrescribedExercise = {
  id: string;
  exercise_id: number;
  slot: number;
  sets: number;
  rep_min: number | null;
  rep_max: number | null;
};

export type PlanSession = {
  id: string;
  position: number;
  name: string;
  max_minutes: number;
  /** ISO weekday, 1 = Monday. */
  weekday: number | null;
  exercises: PrescribedExercise[];
};

export type PlanWeek = {
  id: string;
  week_number: number;
  rir: number;
  is_deload: boolean;
  sessions: PlanSession[];
};

export type MuscleTarget = {
  muscle_id: number;
  priority: number;
};

export type PlanSummary = {
  id: string;
  name: string;
  status: PlanStatus;
  num_weeks: number;
  config_id: number;
  created_at: string;
  updated_at: string;
};

export type PlanDetail = PlanSummary & {
  weeks: PlanWeek[];
  muscle_targets: MuscleTarget[];
};

// ---------------------------------------------------------------------------
// Write
// ---------------------------------------------------------------------------

export type PlanCreate = { name: string; num_weeks?: number };

export type PlanUpdate = { name?: string; num_weeks?: number };

export type PrescribedExerciseWrite = {
  id?: string;
  exercise_id: number;
  sets: number;
  rep_min?: number | null;
  rep_max?: number | null;
};

export type PlanSessionWrite = {
  id?: string;
  name: string;
  max_minutes: number;
  weekday: number | null;
  exercises: PrescribedExerciseWrite[];
};

export type BaseWeekWrite = { sessions: PlanSessionWrite[] };

// ---------------------------------------------------------------------------
// Analysis
// ---------------------------------------------------------------------------

export type MuscleAnalysis = {
  muscle_id: number;
  muscle_code: string;
  volume: number;
  zone: VolumeZone;
  mev: number;
  mav_upper: number;
  mrv: number;
  priority: number;
  benefit: number | null;
  penalty: number | null;
  score: number | null;
};

export type WeekAnalysis = {
  week_number: number;
  rir: number;
  is_deload: boolean;
  volume_score: number;
  overtime_minutes: number;
  session_minutes: number[];
  muscles: MuscleAnalysis[];
};

/** Prescription defaults the analysis assumed - shown next to every exercise. */
export type PlanAssumptions = {
  rep_range_compound: [number, number];
  rep_range_isolation: [number, number];
  default_tempo: string;
};

export type PlanAnalysis = {
  /** "projected": only the base week is saved, later weeks are computed on the fly */
  source: "stored" | "projected";
  score: number;
  max_score: number;
  volume_score: number;
  time_penalty: number;
  assumptions: PlanAssumptions;
  weeks: WeekAnalysis[];
};

export const MAX_SESSIONS_PER_WEEK = 7;
export const MAX_EXERCISES_PER_SESSION = 15;
export const MAX_SETS = 10;