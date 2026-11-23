import { useState, type FormEvent } from "react";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import type { SessionSettings } from "../draft";
import { MinutesSlider } from "./MinutesSlider";
import { WeekdayPicker } from "./WeekdayPicker";

type SessionSettingsDialogProps = {
  title: string;
  initial: SessionSettings;
  /** Weekdays already taken by other sessions - two sessions cannot share a day. */
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
  const [name, setName] = useState(initial.name);
  const [weekday, setWeekday] = useState<number | null>(initial.weekday);
  const [maxMinutes, setMaxMinutes] = useState(initial.maxMinutes);
  const trimmed = name.trim();

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
            <WeekdayPicker value={weekday} onChange={setWeekday} taken={takenWeekdays} />
            <MinutesSlider value={maxMinutes} onChange={setMaxMinutes} />
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
