import { Box, FormHelperText, Slider, Stack, Typography } from "@mui/material";
import { useId } from "react";
import { useTranslation } from "react-i18next";

import { FONT_MONO } from "@/styles/theme";

const LIMIT_OPTIONS = [30, 45, 60, 75, 90, 105, 120, 150, 180];
const LABELLED_LIMITS = new Set([30, 60, 90, 120, 150, 180]);

type MinutesSliderProps = {
  value: number;
  onChange: (minutes: number) => void;
};

/** Time limit of a session, in steps of 15-30 min. */
export function MinutesSlider({ value, onChange }: MinutesSliderProps) {
  const { t } = useTranslation("plans");
  const labelId = useId();

  // Keep a custom limit (e.g. set by the profile) selectable.
  const limits = LIMIT_OPTIONS.includes(value)
    ? LIMIT_OPTIONS
    : [...LIMIT_OPTIONS, value].sort((a, b) => a - b);

  return (
    <Stack spacing={0.5}>
      <Stack direction="row" sx={{ justifyContent: "space-between" }}>
        <Typography id={labelId} variant="body2" sx={{ fontWeight: 500 }}>
          {t("session.limit")}
        </Typography>
        <Typography sx={{ fontFamily: FONT_MONO, fontSize: 13 }}>
          {t("session.limitOption", { minutes: value })}
        </Typography>
      </Stack>
      <Box sx={{ px: 1, pb: 2.5 }}>
        <Slider
          aria-labelledby={labelId}
          value={value}
          onChange={(_, next) => onChange(next)}
          step={null}
          min={limits[0]}
          max={limits[limits.length - 1]}
          marks={limits.map((minutes) => ({
            value: minutes,
            label: LABELLED_LIMITS.has(minutes) ? String(minutes) : undefined,
          }))}
          getAriaValueText={(minutes) => t("session.limitOption", { minutes })}
        />
      </Box>
      <FormHelperText>{t("session.limitHint")}</FormHelperText>
    </Stack>
  );
}