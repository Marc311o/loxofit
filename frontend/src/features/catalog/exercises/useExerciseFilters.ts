import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router";

import {
  MOVEMENT_PATTERNS,
  MUSCLE_GROUPS,
  type ExerciseType,
  type MovementPattern,
  type MuscleGroup,
} from "../types.ts";

const EXERCISE_TYPES: readonly ExerciseType[] = ["compound", "isolation"];

export type ExerciseFilterState = {
  search: string;
  muscleGroup: MuscleGroup | null;
  pattern: MovementPattern | null;
  type: ExerciseType | null;
  mine: boolean;
  page: number;
};

const URL_KEYS = {
  search: "q",
  muscleGroup: "group",
  pattern: "pattern",
  type: "type",
  mine: "mine",
  page: "page",
} as const satisfies Record<keyof ExerciseFilterState, string>;

function parseOption<T extends string>(value: string | null, options: readonly T[]): T | null {
  return options.find((option) => option === value) ?? null;
}

export function useExerciseFilters() {
  const [params, setParams] = useSearchParams();

  const filters = useMemo<ExerciseFilterState>(
    () => ({
      search: params.get(URL_KEYS.search) ?? "",
      muscleGroup: parseOption(params.get(URL_KEYS.muscleGroup), MUSCLE_GROUPS),
      pattern: parseOption(params.get(URL_KEYS.pattern), MOVEMENT_PATTERNS),
      type: parseOption(params.get(URL_KEYS.type), EXERCISE_TYPES),
      mine: params.get(URL_KEYS.mine) === "1",
      page: Math.max(1, Number.parseInt(params.get(URL_KEYS.page) ?? "", 10) || 1),
    }),
    [params],
  );

  const setFilters = useCallback(
    (patch: Partial<ExerciseFilterState>) => {
      setParams(
        (previous) => {
          const next = new URLSearchParams(previous);
          const write = (key: keyof ExerciseFilterState, value: string | null) => {
            if (value) next.set(URL_KEYS[key], value);
            else next.delete(URL_KEYS[key]);
          };

          if (patch.search !== undefined) write("search", patch.search.trim());
          if (patch.muscleGroup !== undefined) write("muscleGroup", patch.muscleGroup);
          if (patch.pattern !== undefined) write("pattern", patch.pattern);
          if (patch.type !== undefined) write("type", patch.type);
          if (patch.mine !== undefined) write("mine", patch.mine ? "1" : null);
          write("page", patch.page && patch.page > 1 ? String(patch.page) : null);
          return next;
        },
        { replace: patch.search !== undefined },
      );
    },
    [setParams],
  );

  const clearFilters = useCallback(() => setParams({}, { replace: false }), [setParams]);

  /** Filters other than the search box - shown as a badge on phones. */
  const activeFilterCount = [
    filters.muscleGroup,
    filters.pattern,
    filters.type,
    filters.mine || null,
  ].filter((value) => value !== null).length;

  const hasActiveFilters = filters.search !== "" || activeFilterCount > 0;

  return {
    filters,
    setFilters,
    clearFilters,
    hasActiveFilters,
    activeFilterCount,
  };
}
