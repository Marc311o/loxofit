import { Box, Radio, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import type { ExperienceLevel } from "../api";

const LEVELS: ExperienceLevel[] = ["beginner", "intermediate", "advanced"];

type ExperiencePickerProps = {
  value: ExperienceLevel | null;
  onChange: (level: ExperienceLevel) => void;
  error?: boolean;
};

/** Training experience as three option cards with a short description each. */
export function ExperiencePicker({ value, onChange, error }: ExperiencePickerProps) {
  const { t } = useTranslation("profile");

  return (
    <Stack component="fieldset" spacing={1} sx={{ border: 0, m: 0, p: 0, minWidth: 0 }}>
      <Typography component="legend" variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
        {t("fields.experience")}
      </Typography>
      {LEVELS.map((level) => {
        const selected = value === level;
        const id = `experience-${level}`;
        return (
          <Box
            key={level}
            component="label"
            htmlFor={id}
            sx={{
              display: "flex",
              gap: 1,
              alignItems: "flex-start",
              p: 1.25,
              border: 1,
              borderRadius: 2,
              cursor: "pointer",
              borderColor: selected ? "primary.main" : error ? "error.main" : "divider",
              bgcolor: selected ? "primary.light" : "transparent",
              transition: "border-color 120ms, background-color 120ms",
              "&:hover": { borderColor: "primary.main" },
              "&:has(:focus-visible)": {
                outline: 2,
                outlineColor: "primary.main",
                outlineOffset: 2,
              },
            }}
          >
            <Radio
              id={id}
              size="small"
              name="experience"
              value={level}
              checked={selected}
              onChange={() => onChange(level)}
              sx={{ p: 0.25 }}
            />
            <Stack sx={{ minWidth: 0 }}>
              <Typography sx={{ fontSize: 15, fontWeight: 600 }}>
                {t(`experience.${level}.label`)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t(`experience.${level}.description`)}
              </Typography>
            </Stack>
          </Box>
        );
      })}
      {error && (
        <Typography variant="caption" color="error">
          {t("fields.experienceRequired")}
        </Typography>
      )}
    </Stack>
  );
}
