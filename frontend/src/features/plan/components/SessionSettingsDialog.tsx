import { useState, type FormEvent } from "react";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  // FormHelperText,
  Slider,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import { FONT_MONO } from "@/styles/theme";
import type { SessionSettings } from "../draft";
import { useWeekdayName } from "../format";

const LIMIT_OPTIONS = [30, 45, 60, 75, 90, 105, 120, 150, 180];
const LABELLED_LIMITS = new Set([30, 60, 90, 120, 150, 180]);
const WEEKDAYS = [1, 2, 3, 4, 5, 6, 7];
/** ToggleButtonGroup values must not be null - "any day" gets its own value. */
const ANY_DAY = 0;

type SessionSettingsDialogProps = {
  title: string;
  initial: SessionSettings;
  takenWeekdays: ReadonlySet<number>;
  onClose: () => void;
  onSave: (settings: SessionSettings) => void;
};

/** Name, day and time limit of a session. Mounted only while open. */
export function SessionSettingsDialog({
  title,
  initial,
  takenWeekdays,
  onClose,
  onSave,
}: SessionSettingsDialogProps) {
  const { t } = useTranslation("plans");
  const weekdayName = useWeekdayName();
  const [name, setName] = useState(initial.name);
  const [weekday, setWeekday] = useState<number | null>(initial.weekday);
  const [maxMinutes, setMaxMinutes] = useState(initial.maxMinutes);
  const trimmed = name.trim();

  const limits = LIMIT_OPTIONS.includes(maxMinutes)
    ? LIMIT_OPTIONS
    : [...LIMIT_OPTIONS, maxMinutes].sort((a, b) => a - b);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (trimmed) onSave({ name: trimmed, weekday, maxMinutes });
  };

  return (
    <Dialog open onClose={onClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit} noValidate>
        <DialogTitle>{title}</DialogTitle>
        <DialogContent>
          <Stack spacing={2.5} sx={{ pt: 1 }}>
            <TextField
              label={t("session.name")}
              value={name}
              onChange={(e) => setName(e.target.value)}
              slotProps={{ htmlInput: { maxLength: 50 } }}
              error={trimmed === ""}
              helperText={trimmed === "" ? t("session.nameRequired") : undefined}
              autoFocus
              fullWidth
            />
            <Stack spacing={1}>
              <Typography id="session-weekday" variant="body2" sx={{ fontWeight: 500 }}>
                {t("session.weekday")}
              </Typography>
              <ToggleButtonGroup
                exclusive
                fullWidth
                size="small"
                aria-labelledby="session-weekday"
                value={weekday ?? ANY_DAY}
                onChange={(_, value: number | null) => {
                  if (value !== null) setWeekday(value === ANY_DAY ? null : value);
                }}
              >
                <ToggleButton value={ANY_DAY} sx={{ flexGrow: 1.6, px: 0.5 }}>
                  {t("session.anyDay")}
                </ToggleButton>
                {WEEKDAYS.map((day) => (
                  <ToggleButton
                    key={day}
                    value={day}
                    disabled={takenWeekdays.has(day)}
                    aria-label={weekdayName(day, "long")}
                    sx={{ px: 0.5 }}
                  >
                    {weekdayName(day).replace(/\.$/, "").toUpperCase()}
                  </ToggleButton>
                ))}
              </ToggleButtonGroup>
            </Stack>
            <Stack spacing={0.5}>
              <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                <Typography id="session-limit" variant="body2" sx={{ fontWeight: 500 }}>
                  {t("session.limit")}
                </Typography>
                <Typography sx={{ fontFamily: FONT_MONO, fontSize: 13 }}>
                  {t("session.limitOption", { minutes: maxMinutes })}
                </Typography>
              </Stack>
              <Box sx={{ px: 1, pb: 2.5 }}>
                <Slider
                  aria-labelledby="session-limit"
                  value={maxMinutes}
                  onChange={(_, value) => setMaxMinutes(value)}
                  step={null}
                  min={limits[0]}
                  max={limits[limits.length - 1]}
                  marks={limits.map((value) => ({
                    value,
                    label: LABELLED_LIMITS.has(value) ? String(value) : undefined,
                  }))}
                  getAriaValueText={(value) => t("session.limitOption", { minutes: value })}
                />
              </Box>
              {/*<FormHelperText>{t("session.limitHint")}</FormHelperText>*/}
            </Stack>
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button onClick={onClose}>{t("actions.cancel")}</Button>
          <Button type="submit" variant="contained" disabled={trimmed === ""}>
            {t("actions.save")}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}