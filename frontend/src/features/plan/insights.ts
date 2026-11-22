import type { ExerciseDetail } from "@/features/catalog/types";
import type { DraftSession } from "./draft";
import type { PlanAnalysis, VolumeZone, WeekAnalysis } from "./types";

// -- score --------------------------------------------------------------------

export function scorePercent(analysis: PlanAnalysis): number {
  if (analysis.max_score <= 0) return 0;
  const pct = (analysis.score / analysis.max_score) * 100;
  return Math.round(Math.min(100, Math.max(0, pct)));
}

export function trainingWeeks(analysis: PlanAnalysis): WeekAnalysis[] {
  return analysis.weeks.filter((w) => !w.is_deload);
}

/** The last training week has the most volume - the one where limits are hit first. */
export function peakWeek(analysis: PlanAnalysis): WeekAnalysis | undefined {
  return trainingWeeks(analysis).at(-1);
}

export type ZoneCounts = Record<VolumeZone, number>;

export function zoneCounts(week: WeekAnalysis): ZoneCounts {
  const counts: ZoneCounts = { below_mev: 0, mev_mav: 0, mav_mrv: 0, above_mrv: 0 };
  week.muscles.filter((m) => m.priority > 0).forEach((m) => counts[m.zone]++);
  return counts;
}

// -- issues -------------------------------------------------------------------

export type PlanIssue =
  | { kind: "aboveMrv"; muscleId: number; week: number; volume: number }
  | { kind: "belowMev"; muscleId: number; volume: number }
  | { kind: "capped"; muscleId: number; week: number; lost: number }
  | { kind: "overtime"; session: number; week: number; minutes: number };


export function planIssues(analysis: PlanAnalysis, sessionLimits: number[]): PlanIssue[] {
  const weeks = trainingWeeks(analysis);
  const issues: PlanIssue[] = [];

  const overMrv = new Set<number>();
  for (const week of weeks) {
    for (const m of week.muscles) {
      if (m.zone === "above_mrv" && m.priority > 0 && !overMrv.has(m.muscle_id)) {
        overMrv.add(m.muscle_id);
        issues.push({
          kind: "aboveMrv",
          muscleId: m.muscle_id,
          week: week.week_number,
          volume: m.volume,
        });
      }
    }
  }

  sessionLimits.forEach((limit, session) => {
    let worst: { week: number; minutes: number } | null = null;
    for (const week of weeks) {
      const over = (week.session_minutes[session] ?? 0) - limit;
      if (over > 0.5 && (worst === null || over > worst.minutes)) {
        worst = { week: week.week_number, minutes: over };
      }
    }
    if (worst) issues.push({ kind: "overtime", session, ...worst });
  });

  const peak = weeks.at(-1);
  peak?.muscles
    .filter((m) => m.zone === "below_mev" && m.priority > 0)
    .forEach((m) => issues.push({ kind: "belowMev", muscleId: m.muscle_id, volume: m.volume }));

  const capped = new Set<number>();
  for (const week of weeks) {
    for (const m of week.muscles) {
      const lost = m.volume - m.effective_volume;
      if (lost > 0.05 && m.priority > 0 && !capped.has(m.muscle_id)) {
        capped.add(m.muscle_id);
        issues.push({ kind: "capped", muscleId: m.muscle_id, week: week.week_number, lost });
      }
    }
  }

  return issues;
}

// -- exercise order -----------------------------------------------------------

function primaryMuscles(exercise: ExerciseDetail): Set<number> {
  return new Set(exercise.muscles.filter((m) => m.role === "primary").map((m) => m.muscle.id));
}

export type OrderHint = { isolationKey: string; compoundKey: string };

/**
 * Isolation exercises placed before a compound that shares a primary muscle,
 * e.g. leg extensions before squats. Not part of the score - research shows
 * order matters for strength in the later exercise, not for hypertrophy.
 */
export function orderHints(
  session: DraftSession,
  details: ReadonlyMap<number, ExerciseDetail>,
): OrderHint[] {
  const hints: OrderHint[] = [];
  session.exercises.forEach((first, i) => {
    const isolation = details.get(first.exerciseId);
    if (!isolation || isolation.is_compound) return;
    const fatigued = primaryMuscles(isolation);
    const compound = session.exercises.slice(i + 1).find((later) => {
      const detail = details.get(later.exerciseId);
      return detail?.is_compound && [...primaryMuscles(detail)].some((m) => fatigued.has(m));
    });
    if (compound) hints.push({ isolationKey: first.key, compoundKey: compound.key });
  });
  return hints;
}

/**
 * Compounds first, then isolation; within each group the technically harder
 * and more fatiguing exercises go earlier. Stable for ties.
 */
export function recommendedOrder(
  session: DraftSession,
  details: ReadonlyMap<number, ExerciseDetail>,
): string[] {
  const rank = (exerciseId: number) => {
    const d = details.get(exerciseId);
    return d ? [d.is_compound ? 0 : 1, -d.complexity, -d.fatigue_cost] : [2, 0, 0];
  };
  return session.exercises
    .map((e, index) => ({ key: e.key, rank: rank(e.exerciseId), index }))
    .sort((a, b) => {
      for (let i = 0; i < a.rank.length; i++) {
        if (a.rank[i] !== b.rank[i]) return a.rank[i] - b.rank[i];
      }
      return a.index - b.index;
    })
    .map((e) => e.key);
}