import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { planKeys } from "@/features/plan/api";
import type { PlanAnalysis, PlanDetail } from "@/features/plan/types";
import { api } from "@/lib/api";
import type { GenerationRequest, GenerationRun } from "./types";

/** How often a run in progress is asked for its progress. */
export const POLL_MS = 300;

export const generatorKeys = {
  all: ["generator"] as const,
  run: (id: string) => [...generatorKeys.all, "run", id] as const,
  analysis: (id: string) => [...generatorKeys.all, "analysis", id] as const,
};

export const isActive = (run: GenerationRun | undefined) =>
  run?.status === "queued" || run?.status === "running";

/** A generation run; polled while it is queued or running, then left alone. */
export function useGenerationRun(id: string | null) {
  return useQuery({
    queryKey: generatorKeys.run(id ?? ""),
    queryFn: () => api.get<GenerationRun>(`/generator/runs/${id}`),
    enabled: id !== null,
    refetchInterval: (query) => (isActive(query.state.data) ? POLL_MS : false),
    refetchIntervalInBackground: false,
  });
}

/** The generated plan scored like a saved one - for the analysis panel. */
export function useGenerationAnalysis(id: string | null, options: { enabled: boolean }) {
  return useQuery({
    queryKey: generatorKeys.analysis(id ?? ""),
    queryFn: () => api.get<PlanAnalysis>(`/generator/runs/${id}/analysis`),
    enabled: id !== null && options.enabled,
    staleTime: Infinity, // a finished run never changes
  });
}

export function useStartGeneration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: GenerationRequest) => api.post<GenerationRun>("/generator/runs", request),
    onSuccess: (run) => queryClient.setQueryData(generatorKeys.run(run.id), run),
    meta: { silent: true }, // the form shows the error
  });
}

export function useSaveGeneratedPlan(runId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => api.post<PlanDetail>(`/generator/runs/${runId}/plan`, { name }),
    onSuccess: (plan) => {
      queryClient.setQueryData(planKeys.detail(plan.id), plan);
      void queryClient.invalidateQueries({ queryKey: planKeys.list() });
      void queryClient.invalidateQueries({ queryKey: generatorKeys.run(runId) });
    },
    meta: { silent: true }, // the save dialog shows the error
  });
}