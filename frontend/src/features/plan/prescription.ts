import type { ExerciseDetail } from "@/features/catalog/types";
import type { PlanAssumptions } from "./types";

export type Prescription = {
  repRange: [number, number];
  tempo: string;
};

/**
 * Reps and tempo for one exercise: the rep range of its type (compound or
 * isolation) and its own tempo, else the default one. Read-only for now -
 * the same values the time estimate assumes.
 */
export function prescriptionFor(
  exercise: ExerciseDetail,
  assumptions: PlanAssumptions,
): Prescription {
  return {
    repRange: exercise.is_compound
      ? assumptions.rep_range_compound
      : assumptions.rep_range_isolation,
    tempo: exercise.default_tempo ?? assumptions.default_tempo,
  };
}
