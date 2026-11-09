import type { ReactNode } from "react";
import DirectionsRunRounded from "@mui/icons-material/DirectionsRunRounded";
import FitnessCenterRounded from "@mui/icons-material/FitnessCenterRounded";

import { MuscleIcon } from "@/components/icons/MuscleIcon";

export type CatalogSection = {
  /** Route segment under /catalog and key in `catalog.tabs`. */
  id: "exercises" | "muscles" | "equipment";
  icon: ReactNode;
};

export const CATALOG_SECTIONS: CatalogSection[] = [
  { id: "exercises", icon: <DirectionsRunRounded /> },
  { id: "muscles", icon: <MuscleIcon /> },
  { id: "equipment", icon: <FitnessCenterRounded /> },
];
