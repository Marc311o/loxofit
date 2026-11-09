import { Box, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { useFormatNumber, useLocalizedName } from "@/i18n/useLocalized.ts";
import { FONT_MONO, zoneColors } from "@/styles/theme.ts";
import type { MuscleRole, MuscleShare } from "../../types.ts";

const ROLE_COLORS: Record<MuscleRole, string> = {
  primary: zoneColors.mavMrv,
  secondary: zoneColors.mevMav,
  stabilizer: zoneColors.belowMev,
};

export function MuscleShareList({ muscles }: { muscles: MuscleShare[] }) {
  const { t } = useTranslation("catalog");
  const localizedName = useLocalizedName();
  const formatNumber = useFormatNumber();

  return (
    <Stack spacing={1.75}>
      {muscles.map((share) => (
        <Box key={share.muscle.id}>
          <Stack
            direction="row"
            spacing={2}
            sx={{ justifyContent: "space-between", alignItems: "baseline" }}
          >
            <Typography variant="body2">
              <Box component="span" sx={{ fontWeight: 600 }}>
                {localizedName(share.muscle)}
              </Box>
              <Box component="span" sx={{ color: "text.secondary" }}>
                {" · "}
                {t(`roles.${share.role}`)}
              </Box>
            </Typography>
            <Typography
              variant="body2"
              sx={{
                fontFamily: FONT_MONO,
                fontSize: 13,
                color: "text.secondary",
              }}
            >
              {formatNumber(Math.round(share.share_pct))}%
            </Typography>
          </Stack>
          <Box
            sx={{
              mt: 0.75,
              height: 8,
              borderRadius: 4,
              bgcolor: "divider",
              overflow: "hidden",
            }}
          >
            <Box
              sx={{
                width: `${Math.min(share.weight, 1) * 100}%`,
                height: "100%",
                borderRadius: 4,
                bgcolor: ROLE_COLORS[share.role],
              }}
            />
          </Box>
        </Box>
      ))}
    </Stack>
  );
}
