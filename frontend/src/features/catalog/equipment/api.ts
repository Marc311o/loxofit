import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Equipment } from "../types";

export const myEquipmentKey = ["users", "me", "equipment"] as const;

export function useMyEquipment() {
  return useQuery({
    queryKey: myEquipmentKey,
    queryFn: () => api.get<Equipment[]>("/users/me/equipment"),
  });
}
