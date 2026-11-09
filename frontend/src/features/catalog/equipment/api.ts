import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { CATALOG_STALE_TIME, catalogKeys } from "../queryKeys";
import type { Equipment } from "../types";

export const equipmentKeys = {
  all: [...catalogKeys.all, "equipment"] as const,
};

/**
 * The user's own equipment is user data, not catalog data, so it does not live
 * under the catalog root - refreshing the catalog must not refetch it and vice versa.
 */
export const myEquipmentKey = ["users", "me", "equipment"] as const;

/** Every piece of equipment in the catalog, ordered by category. */
export function useEquipmentCatalog() {
  return useQuery({
    queryKey: equipmentKeys.all,
    queryFn: () => api.get<Equipment[]>("/equipment"),
    staleTime: CATALOG_STALE_TIME,
  });
}

/** Equipment the signed-in user has access to. */
export function useMyEquipment() {
  return useQuery({
    queryKey: myEquipmentKey,
    queryFn: () => api.get<Equipment[]>("/users/me/equipment"),
  });
}

/** Replaces the user's equipment; the response becomes the new cached value. */
export function useSaveMyEquipment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (equipmentIds: number[]) =>
      api.put<Equipment[]>("/users/me/equipment", {
        equipment_ids: equipmentIds,
      }),
    onSuccess: (saved) => queryClient.setQueryData(myEquipmentKey, saved),
  });
}
