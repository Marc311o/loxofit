/**
 * Drag and drop of exercises in the base-week editor: within a session to
 * reorder, between sessions to move. Pure helpers - the editor wires them to dnd-kit.
 */
import { arrayMove } from "@dnd-kit/sortable";

import { canMoveTo, type Draft, moveExercise, reorderExercises } from "./draft";

const SESSION_PREFIX = "session:";

/** Drop target id of a whole session - lets exercises land in an empty one. */
export const sessionDropId = (sessionKey: string) => `${SESSION_PREFIX}${sessionKey}`;

/** What a dragged exercise carries. */
export type DragData = { sessionKey: string };

/** The session under the pointer: a session itself, or the session of the exercise there. */
export function targetSession(overId: string, overData: unknown): string | undefined {
  if (overId.startsWith(SESSION_PREFIX)) return overId.slice(SESSION_PREFIX.length);
  return (overData as DragData | undefined)?.sessionKey;
}

export type DropResult = { draft: Draft } | { refused: true } | null;

/**
 * Where `exerciseKey` lands when dropped on `overId`:
 * the same session reorders, another session moves it before the exercise
 * it was dropped on (or to the end when dropped on the session).
 * `null` - nothing to change; `refused` - the target cannot take it.
 */
export function applyDrop(
  draft: Draft,
  exerciseKey: string,
  fromKey: string,
  overId: string,
  toKey: string,
): DropResult {
  const from = draft.sessions.find((s) => s.key === fromKey);
  const to = draft.sessions.find((s) => s.key === toKey);
  if (!from || !to) return null;

  if (fromKey === toKey) {
    const keys = from.exercises.map((e) => e.key);
    const oldIndex = keys.indexOf(exerciseKey);
    const newIndex = keys.indexOf(overId);
    if (oldIndex < 0 || newIndex < 0 || oldIndex === newIndex) return null;
    return { draft: reorderExercises(draft, fromKey, arrayMove(keys, oldIndex, newIndex)) };
  }

  const exercise = from.exercises.find((e) => e.key === exerciseKey);
  if (!exercise) return null;
  if (!canMoveTo(to, exercise.exerciseId)) return { refused: true };
  const index = to.exercises.findIndex((e) => e.key === overId);
  return {
    draft: moveExercise(draft, fromKey, exerciseKey, toKey, index < 0 ? undefined : index),
  };
}
