import { useOutletContext } from "react-router";

import type { PlanDetail } from "./types";

export type PlanOutletContext = { plan: PlanDetail };

/** The plan loaded by `PlanLayout`, for its tab pages. */
export function usePlanOutlet() {
  return useOutletContext<PlanOutletContext>();
}
