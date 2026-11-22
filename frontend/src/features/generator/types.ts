import type { MuscleTarget } from "@/features/plan/types";

export type SplitTemplate = "full_body" | "upper_lower" | "push_pull_legs" | "custom";

export type Focus = "full_body" | "upper" | "lower" | "push" | "pull";

export type GenerationStatus = "queued" | "running" | "done" | "failed";

// ---------------------------------------------------------------------------
// Request
// ---------------------------------------------------------------------------

export type SessionRequest = {
  /** null - the backend names it after the focus. */
  name: string | null;
  weekday: number | null;
  max_minutes: number;
  /** Custom template only - otherwise the template decides. */
  focus: Focus | null;
};

export type GenerationRequest = {
  template: SplitTemplate;
  sessions: SessionRequest[];
  num_weeks: number;
  targets: MuscleTarget[];
  /** null - a new random plan every time. */
  seed: number | null;
};

// ---------------------------------------------------------------------------
// Read
// ---------------------------------------------------------------------------

export type GenerationProgress = {
  evaluations: number;
  budget: number;
  best_score: number | null;
};

export type GeneratedExercise = { exercise_id: number; sets: number };

export type GeneratedSession = {
  name: string;
  weekday: number | null;
  max_minutes: number;
  focus: Focus;
  exercises: GeneratedExercise[];
};

export type GenerationRun = {
  id: string;
  status: GenerationStatus;
  request: GenerationRequest;
  seed: number;
  algorithm: string;
  budget: number;
  config_id: number;
  /** While queued or running. */
  progress: GenerationProgress | null;
  evaluations: number | null;
  score: number | null;
  /** Known from the start - scores are shown as % of it. */
  max_score: number | null;
  /** When done. */
  sessions: GeneratedSession[] | null;
  /** [evaluations, best score] at every improvement. */
  history: [number, number][] | null;
  error: string | null;
  /** Set once the generated plan has been saved. */
  plan_id: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
};

/** Limits mirrored from the backend validation. */
export const MIN_WEEKS = 2;
export const MAX_WEEKS = 12;