import AddRounded from "@mui/icons-material/AddRounded";
import RemoveRounded from "@mui/icons-material/RemoveRounded";
import { IconButton, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { FONT_MONO } from "@/styles/theme";
import { MAX_SETS } from "../types";

type SetsStepperProps = {
  value: number;
  /** Name of the exercise, for screen readers ("Fewer sets: Bench press"). */
  label: string;
  onChange: (sets: number) => void;
};

export function SetsStepper({ value, label, onChange }: SetsStepperProps) {
  const { t } = useTranslation("plans");

  return (
    <Stack
      direction="row"
      role="group"
      aria-label={t("editor.setsOf", { exercise: label })}
      sx={{
        alignItems: "center",
        border: 1,
        borderColor: "divider",
        borderRadius: 2.5,
        height: 36,
        flexShrink: 0,
      }}
    >
      <IconButton
        size="small"
        aria-label={t("editor.fewerSets")}
        disabled={value <= 1}
        onClick={() => onChange(value - 1)}
      >
        <RemoveRounded fontSize="small" />
      </IconButton>
      <Typography
        aria-live="polite"
        sx={{ width: 24, textAlign: "center", fontFamily: FONT_MONO, fontSize: 13 }}
      >
        {value}
      </Typography>
      <IconButton
        size="small"
        aria-label={t("editor.moreSets")}
        disabled={value >= MAX_SETS}
        onClick={() => onChange(value + 1)}
      >
        <AddRounded fontSize="small" />
      </IconButton>
    </Stack>
  );
}