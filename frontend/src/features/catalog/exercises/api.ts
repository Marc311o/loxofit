import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Page } from "@/lib/pagination";
import { catalogKeys } from "../queryKeys";
import type {
  ExerciseCountQuery,
  ExerciseDetail,
  ExerciseQuery,
  ExerciseSummary,
  MuscleGroup,
} from "../types";

export const EXERCISE_PAGE_SIZE = 20;

/** Catalog data only changes with a new seed, so it can stay fresh for a long time. */
const CATALOG_STALE_TIME = 30 * 60 * 1000;

export const exerciseKeys = {
  all: [...catalogKeys.all, "exercises"] as const,
  list: (query: ExerciseQuery) => [...exerciseKeys.all, "list", query] as const,
  groupCounts: (query: ExerciseCountQuery) => [...exerciseKeys.all, "group-counts", query] as const,
  detail: (id: number) => [...exerciseKeys.all, "detail", id] as const,
};

/** Filters shared by the list and the per-group counts. */
function filterParams(query: ExerciseCountQuery): URLSearchParams {
  const params = new URLSearchParams();
  if (query.search) params.set("search", query.search);
  if (query.pattern) params.set("pattern", query.pattern);
  if (query.type) params.set("is_compound", String(query.type === "compound"));
  query.availableWith?.forEach((id) => params.append("available_with", String(id)));
  return params;
}

function exerciseSearchParams(query: ExerciseQuery): URLSearchParams {
  const params = filterParams(query);
  params.set("page", String(query.page));
  params.set("size", String(EXERCISE_PAGE_SIZE));
  params.set("sort", query.sort);
  if (query.muscleGroup) params.set("muscle_group", query.muscleGroup);
  return params;
}

export function useExercises(query: ExerciseQuery, options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: exerciseKeys.list(query),
    queryFn: () => api.get<Page<ExerciseSummary>>(`/exercises?${exerciseSearchParams(query)}`),
    placeholderData: keepPreviousData,
    staleTime: CATALOG_STALE_TIME,
    enabled: options.enabled ?? true,
  });
}

export function useExerciseGroupCounts(
  query: ExerciseCountQuery,
  options: { enabled?: boolean } = {},
) {
  return useQuery({
    queryKey: exerciseKeys.groupCounts(query),
    queryFn: () =>
      api.get<Record<MuscleGroup, number>>(`/exercises/group-counts?${filterParams(query)}`),
    placeholderData: keepPreviousData,
    staleTime: CATALOG_STALE_TIME,
    enabled: options.enabled ?? true,
  });
}

export function useExercise(id: number | null) {
  return useQuery({
    queryKey: exerciseKeys.detail(id ?? 0),
    queryFn: () => api.get<ExerciseDetail>(`/exercises/${id}`),
    staleTime: CATALOG_STALE_TIME,
    enabled: id !== null,
  });
}
