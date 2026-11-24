import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, ApiError } from "@/lib/api";
import type {
  BaseWeekWrite,
  PlanAnalysis,
  PlanCreate,
  PlanDetail,
  PlanSummary,
  PlanUpdate,
} from "./types";

export const planKeys = {
  all: ["plans"] as const,
  list: () => [...planKeys.all, "list"] as const,
  active: () => [...planKeys.all, "active"] as const,
  detail: (id: string) => [...planKeys.all, "detail", id] as const,
  analysis: (id: string) => [...planKeys.all, "analysis", id] as const,
};

export function usePlans() {
  return useQuery({
    queryKey: planKeys.list(),
    queryFn: () => api.get<PlanSummary[]>("/plans"),
  });
}

export function usePlan(id: string) {
  return useQuery({
    queryKey: planKeys.detail(id),
    queryFn: () => api.get<PlanDetail>(`/plans/${id}`),
  });
}

/** The active plan, or `null` when the user has none (404 NO_ACTIVE_PLAN). */
export function useActivePlan() {
  return useQuery({
    queryKey: planKeys.active(),
    queryFn: async () => {
      try {
        return await api.get<PlanDetail>("/plans/active");
      } catch (error) {
        if (error instanceof ApiError && error.code === "NO_ACTIVE_PLAN") return null;
        throw error;
      }
    },
  });
}

export function usePlanAnalysis(id: string, options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: planKeys.analysis(id),
    queryFn: () => api.get<PlanAnalysis>(`/plans/${id}/analysis`),
    enabled: options.enabled ?? true,
  });
}

/** Saves the base week. Used by the editor's autosave, outside of a mutation hook. */
export function saveBaseWeek(id: string, week: BaseWeekWrite) {
  return api.put<PlanDetail>(`/plans/${id}/base-week`, week);
}

/** A changed plan: new detail in the cache, everything derived from it refetched. */
function usePlanChanged() {
  const queryClient = useQueryClient();
  return (plan: PlanDetail) => {
    queryClient.setQueryData(planKeys.detail(plan.id), plan);
    void queryClient.invalidateQueries({ queryKey: planKeys.analysis(plan.id) });
    void queryClient.invalidateQueries({ queryKey: planKeys.list() });
    void queryClient.invalidateQueries({ queryKey: planKeys.active() });
  };
}

export function useCreatePlan() {
  const onChanged = usePlanChanged();
  return useMutation({
    mutationFn: (data: PlanCreate) => api.post<PlanDetail>("/plans", data),
    onSuccess: onChanged,
  });
}

export function useUpdatePlan(id: string) {
  const onChanged = usePlanChanged();
  return useMutation({
    mutationFn: (data: PlanUpdate) => api.patch<PlanDetail>(`/plans/${id}`, data),
    onSuccess: onChanged,
  });
}

export function useActivatePlan(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<PlanDetail>(`/plans/${id}/activate`),
    // Activation archives the previous active plan, so every plan query is stale.
    onSuccess: () => queryClient.invalidateQueries({ queryKey: planKeys.all }),
  });
}

export function useGenerateProgression(id: string) {
  const onChanged = usePlanChanged();
  return useMutation({
    mutationFn: () => api.post<PlanDetail>(`/plans/${id}/progression`),
    onSuccess: onChanged,
  });
}

export function useDeletePlan(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.delete<void>(`/plans/${id}`),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: planKeys.detail(id) });
      queryClient.removeQueries({ queryKey: planKeys.analysis(id) });
      void queryClient.invalidateQueries({ queryKey: planKeys.list() });
      void queryClient.invalidateQueries({ queryKey: planKeys.active() });
    },
  });
}
