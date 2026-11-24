import { Stack, ToggleButton, ToggleButtonGroup, Typography } from "@mui/material";
import { useId } from "react";
import { useTranslation } from "react-i18next";

import { useWeekdayName } from "../format";

const WEEKDAYS = [1, 2, 3, 4, 5, 6, 7];
/** ToggleButtonGroup values must not be null - "any day" gets its own value. */
const ANY_DAY = 0;

type WeekdayPickerProps = {
  /** ISO weekday (1 = Monday) or null - any day. */
  value: number | null;
  onChange: (weekday: number | null) => void;
  /** Days taken by other sessions - two sessions cannot share a day. */
  taken?: ReadonlySet<number>;
};

/** "Any day" plus the seven weekdays, as one row of toggle buttons. */
export function WeekdayPicker({ value, onChange, taken }: WeekdayPickerProps) {
  const { t } = useTranslation("plans");
  const weekdayName = useWeekdayName();
  const labelId = useId();

  return (
    <Stack spacing={1}>
      <Typography id={labelId} variant="body2" sx={{ fontWeight: 500 }}>
        {t("session.weekday")}
      </Typography>
      <ToggleButtonGroup
        exclusive
        fullWidth
        size="small"
        aria-labelledby={labelId}
        value={value ?? ANY_DAY}
        onChange={(_, next: number | null) => {
          if (next !== null) onChange(next === ANY_DAY ? null : next);
        }}
      >
        <ToggleButton value={ANY_DAY} sx={{ flexGrow: 1.6, px: 0.5 }}>
          {t("session.anyDay")}
        </ToggleButton>
        {WEEKDAYS.map((day) => (
          <ToggleButton
            key={day}
            value={day}
            disabled={taken?.has(day) ?? false}
            aria-label={weekdayName(day, "long")}
            sx={{ px: 0.5 }}
          >
            {weekdayName(day).replace(/\.$/, "").toUpperCase()}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>
    </Stack>
  );
}
