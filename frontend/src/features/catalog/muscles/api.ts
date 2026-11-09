import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { CATALOG_STALE_TIME, catalogKeys } from "../queryKeys";
import type { Muscle } from "../types";

export const muscleKeys = {
  all: [...catalogKeys.all, "muscles"] as const,
};

/** All muscles, ordered by group and English name. */
export function useMuscles() {
  return useQuery({
    queryKey: muscleKeys.all,
    queryFn: () => api.get<Muscle[]>("/muscles"),
    staleTime: CATALOG_STALE_TIME,
  });
}
