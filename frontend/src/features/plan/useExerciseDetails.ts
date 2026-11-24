import { useQueries } from "@tanstack/react-query";

import { exerciseQueryOptions } from "@/features/catalog/exercises/api";
import type { ExerciseDetail } from "@/features/catalog/types";

/**
 * Details (names, muscle roles, complexity) of every exercise in a plan, by id.
 * One cached request per exercise - shared with the catalog's detail dialog.
 */
export function useExerciseDetails(ids: Iterable<number>) {
  const unique = [...new Set(ids)].sort((a, b) => a - b);
  return useQueries({
    queries: unique.map((id) => exerciseQueryOptions(id)),
    combine: (results) => ({
      details: new Map(
        results.flatMap((r): [number, ExerciseDetail][] => (r.data ? [[r.data.id, r.data]] : [])),
      ),
      isPending: results.some((r) => r.isPending),
    }),
  });
}
