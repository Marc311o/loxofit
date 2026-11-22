import { useState, type FormEvent } from "react";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import { MinutesSlider } from "@/features/plan/components/MinutesSlider";
import { WeekdayPicker } from "@/features/plan/components/WeekdayPicker";
import type { FormSession } from "../request";
import type { Focus } from "../types";

const FOCUSES: Focus[] = ["full_body", "upper", "lower", "push", "pull"];

type SessionRequestDialogProps = {
  session: FormSession;
  /** The name it gets when left empty. */
  defaultName: string;
  /** The custom template lets the user pick the focus. */
  editFocus: boolean;
  takenWeekdays: ReadonlySet<number>;
  onClose: () => void;
  onSave: (change: Omit<FormSession, "key">) => void;
};

/** Day, time limit, optional name and - in a custom split - the focus of one session. */
export function SessionRequestDialog({
  session,
  defaultName,
  editFocus,
  takenWeekdays,
  onClose,
  onSave,
}: SessionRequestDialogProps) {
  const { t } = useTranslation(["generator", "plans"]);
  const [name, setName] = useState(session.name);
  const [weekday, setWeekday] = useState(session.weekday);
  const [maxMinutes, setMaxMinutes] = useState(session.maxMinutes);
  const [focus, setFocus] = useState(session.focus);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSave({ name: name.trim(), weekday, maxMinutes, focus });
  };

  return (
    <Dialog open onClose={onClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit} noValidate>
        <DialogTitle>{t("form.editSession", { session: name.trim() || defaultName })}</DialogTitle>
        <DialogContent>
          <Stack spacing={2.5} sx={{ pt: 1 }}>
            {editFocus && (
              <TextField
                select
                label={t("focus.label")}
                value={focus}
                onChange={(e) => setFocus(e.target.value as Focus)}
                fullWidth
              >
                {FOCUSES.map((f) => (
                  <MenuItem key={f} value={f}>
                    {t(`focus.${f}`)}
                  </MenuItem>
                ))}
              </TextField>
            )}
            <TextField
              label={t("form.sessionName")}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={defaultName}
              helperText={t("form.sessionNameHint", { name: defaultName })}
              slotProps={{ htmlInput: { maxLength: 50 }, inputLabel: { shrink: true } }}
              fullWidth
            />
            <WeekdayPicker value={weekday} onChange={setWeekday} taken={takenWeekdays} />
            <MinutesSlider value={maxMinutes} onChange={setMaxMinutes} />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button onClick={onClose}>{t("plans:actions.cancel")}</Button>
          <Button type="submit" variant="contained">
            {t("plans:actions.save")}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}