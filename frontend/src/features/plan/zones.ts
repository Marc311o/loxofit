import { zoneColors } from "@/styles/theme";
import type { VolumeZone } from "./types";

export const ZONE_COLOR: Record<VolumeZone, string> = {
  below_mev: zoneColors.belowMev,
  mev_mav: zoneColors.mevMav,
  mav_mrv: zoneColors.mavMrv,
  above_mrv: zoneColors.aboveMrv,
};