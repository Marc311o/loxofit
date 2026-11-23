import AddRounded from "@mui/icons-material/AddRounded";
import RemoveRounded from "@mui/icons-material/RemoveRounded";
import {
  FormHelperText,
  IconButton,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { useId } from "react";
import { useTranslation } from "react-i18next";

import { MinutesSlider } from "@/features/plan/components/MinutesSlider";
import { useWeekdayName } from "@/features/plan/format";
import { FONT_MONO } from "@/styles/theme";
import type { ProfileForm } from "../form";

const WEEKDAYS = [1, 2, 3, 4, 5, 6, 7];

type TrainingFieldsProps = {
  form: ProfileForm;
  onChange: (change: Partial<ProfileForm>) => void;
};

/** How the user trains: sessions per week, preferred days and the time of a session. */
export function TrainingFields({ form, onChange }: TrainingFieldsProps) {
  const { t } = useTranslation("profile");
  const weekdayName = useWeekdayName();
  const daysId = useId();
  const weekdaysId = useId();
  const tooManyDays = form.weekdays.length > 0 && form.weekdays.length !== form.daysPerWeek;

  return (
    <Stack spacing={3}>
      <Stack direction="row" sx={{ alignItems: "center", justifyContent: "space-between" }}>
        <Typography id={daysId} variant="body2" sx={{ fontWeight: 600 }}>
          {t("fields.daysPerWeek")}
        </Typography>
        <Stack
          direction="row"
          role="group"
          aria-labelledby={daysId}
          sx={{ alignItems: "center", border: 1, borderColor: "divider", borderRadius: 2 }}
        >
          <IconButton
            size="small"
            aria-label={t("fields.fewerDays")}
            disabled={form.daysPerWeek <= 1}
            onClick={() => onChange({ daysPerWeek: form.daysPerWeek - 1 })}
          >
            <RemoveRounded fontSize="small" />
          </IconButton>
          <Typography
            aria-live="polite"
            sx={{ fontFamily: FONT_MONO, fontSize: 15, minWidth: 24, textAlign: "center" }}
          >
            {form.daysPerWeek}
          </Typography>
          <IconButton
            size="small"
            aria-label={t("fields.moreDays")}
            disabled={form.daysPerWeek >= 7}
            onClick={() => onChange({ daysPerWeek: form.daysPerWeek + 1 })}
          >
            <AddRounded fontSize="small" />
          </IconButton>
        </Stack>
      </Stack>

      <Stack spacing={1}>
        <Typography id={weekdaysId} variant="body2" sx={{ fontWeight: 600 }}>
          {t("fields.weekdays")}
        </Typography>
        <ToggleButtonGroup
          fullWidth
          size="small"
          aria-labelledby={weekdaysId}
          value={form.weekdays}
          onChange={(_, days: number[]) => onChange({ weekdays: days })}
        >
          {WEEKDAYS.map((day) => (
            <ToggleButton
              key={day}
              value={day}
              aria-label={weekdayName(day, "long")}
              sx={{ px: 0 }}
            >
              {weekdayName(day).replace(/\.$/, "").toUpperCase()}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
        <FormHelperText>
          {tooManyDays
            ? t("fields.weekdaysMismatch", { count: form.daysPerWeek })
            : t("fields.weekdaysHint")}
        </FormHelperText>
      </Stack>

      <MinutesSlider value={form.minutes} onChange={(minutes) => onChange({ minutes })} />
    </Stack>
  );
}
