import {
  type BaseWeekWrite,
  MAX_EXERCISES_PER_SESSION,
  type PlanDetail,
  type PlanWeek,
} from "./types";

export type DraftExercise = {
  key: string;
  id?: string;
  exerciseId: number;
  sets: number;
  repMin: number | null;
  repMax: number | null;
};

export type DraftSession = {
  key: string;
  id?: string;
  name: string;
  maxMinutes: number;
  weekday: number | null;
  exercises: DraftExercise[];
};

export type Draft = { sessions: DraftSession[] };

export type SessionSettings = Pick<DraftSession, "name" | "maxMinutes" | "weekday">;

export const DEFAULT_SETS = 3;
export const DEFAULT_MAX_MINUTES = 60;

const newKey = () => crypto.randomUUID();

export function fromWeek(week: PlanWeek | undefined): Draft {
  return {
    sessions: (week?.sessions ?? []).map((s) => ({
      key: s.id,
      id: s.id,
      name: s.name,
      maxMinutes: s.max_minutes,
      weekday: s.weekday,
      exercises: s.exercises.map((e) => ({
        key: e.id,
        id: e.id,
        exerciseId: e.exercise_id,
        sets: e.sets,
        repMin: e.rep_min,
        repMax: e.rep_max,
      })),
    })),
  };
}

export function toWrite(draft: Draft): BaseWeekWrite {
  return {
    sessions: draft.sessions.map((s) => ({
      id: s.id,
      name: s.name,
      max_minutes: s.maxMinutes,
      weekday: s.weekday,
      exercises: s.exercises.map((e) => ({
        id: e.id,
        exercise_id: e.exerciseId,
        sets: e.sets,
        rep_min: e.repMin,
        rep_max: e.repMax,
      })),
    })),
  };
}

export function applyServerIds(current: Draft, sent: Draft, saved: PlanDetail): Draft {
  const ids = new Map<string, string>();
  const week = saved.weeks[0];
  sent.sessions.forEach((session, i) => {
    const savedSession = week?.sessions[i];
    if (!savedSession) return;
    ids.set(session.key, savedSession.id);
    session.exercises.forEach((exercise, j) => {
      const savedExercise = savedSession.exercises[j];
      if (savedExercise) ids.set(exercise.key, savedExercise.id);
    });
  });
  return {
    sessions: current.sessions.map((s) => ({
      ...s,
      id: s.id ?? ids.get(s.key),
      exercises: s.exercises.map((e) => ({ ...e, id: e.id ?? ids.get(e.key) })),
    })),
  };
}

// -- sessions -----------------------------------------------------------------

export function addSession(draft: Draft, settings: SessionSettings): Draft {
  return {
    sessions: [...draft.sessions, { key: newKey(), ...settings, exercises: [] }],
  };
}

export function updateSession(draft: Draft, key: string, settings: SessionSettings): Draft {
  return {
    sessions: draft.sessions.map((s) => (s.key === key ? { ...s, ...settings } : s)),
  };
}

export function removeSession(draft: Draft, key: string): Draft {
  return { sessions: draft.sessions.filter((s) => s.key !== key) };
}

// -- exercises ----------------------------------------------------------------

function mapSession(draft: Draft, key: string, change: (s: DraftSession) => DraftSession): Draft {
  return { sessions: draft.sessions.map((s) => (s.key === key ? change(s) : s)) };
}

export function addExercise(draft: Draft, sessionKey: string, exerciseId: number): Draft {
  return mapSession(draft, sessionKey, (s) => ({
    ...s,
    exercises: [
      ...s.exercises,
      { key: newKey(), exerciseId, sets: DEFAULT_SETS, repMin: null, repMax: null },
    ],
  }));
}

export function removeExercise(draft: Draft, sessionKey: string, exerciseKey: string): Draft {
  return mapSession(draft, sessionKey, (s) => ({
    ...s,
    exercises: s.exercises.filter((e) => e.key !== exerciseKey),
  }));
}

export function setSets(draft: Draft, sessionKey: string, exerciseKey: string, sets: number) {
  return mapSession(draft, sessionKey, (s) => ({
    ...s,
    exercises: s.exercises.map((e) => (e.key === exerciseKey ? { ...e, sets } : e)),
  }));
}

export function moveExercise(
  draft: Draft,
  fromKey: string,
  exerciseKey: string,
  toKey: string,
  index?: number,
): Draft {
  const exercise = draft.sessions
    .find((s) => s.key === fromKey)
    ?.exercises.find((e) => e.key === exerciseKey);
  const target = draft.sessions.find((s) => s.key === toKey);
  if (!exercise || !target || fromKey === toKey || !canMoveTo(target, exercise.exerciseId)) {
    return draft;
  }
  const moved: DraftExercise = { ...exercise, key: newKey(), id: undefined };
  return mapSession(removeExercise(draft, fromKey, exerciseKey), toKey, (s) => {
    const exercises = [...s.exercises];
    exercises.splice(index ?? exercises.length, 0, moved);
    return { ...s, exercises };
  });
}

/** A session holds each exercise once and at most MAX_EXERCISES_PER_SESSION of them. */
export function canMoveTo(session: DraftSession, exerciseId: number): boolean {
  return (
    session.exercises.length < MAX_EXERCISES_PER_SESSION &&
    !session.exercises.some((e) => e.exerciseId === exerciseId)
  );
}

export function reorderExercises(draft: Draft, sessionKey: string, orderedKeys: string[]) {
  return mapSession(draft, sessionKey, (s) => {
    const byKey = new Map(s.exercises.map((e) => [e.key, e]));
    return { ...s, exercises: orderedKeys.flatMap((key) => byKey.get(key) ?? []) };
  });
}

export function hasExercises(draft: Draft): boolean {
  return draft.sessions.some((s) => s.exercises.length > 0);
}
