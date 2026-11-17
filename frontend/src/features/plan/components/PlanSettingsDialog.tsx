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

import type { PlanDetail, PlanUpdate } from "../types";

const WEEK_OPTIONS = Array.from({ length: 11 }, (_, i) => i + 2); // 2-12, as the backend allows

type PlanSettingsDialogProps = {
  plan: PlanDetail;
  open: boolean;
  saving: boolean;
  onClose: () => void;
  onSave: (update: PlanUpdate) => void;
};

/** Name and length of the mesocycle. Mounted only while open, so the form starts fresh. */
export function PlanSettingsDialog({
  plan,
  open,
  saving,
  onClose,
  onSave,
}: PlanSettingsDialogProps) {
  const { t } = useTranslation("plans");
  const [name, setName] = useState(plan.name);
  const [weeks, setWeeks] = useState(plan.num_weeks);
  const trimmed = name.trim();
  const weeksChanged = weeks !== plan.num_weeks;
  const hasGeneratedWeeks = plan.weeks.length > 1;

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const update: PlanUpdate = {};
    if (trimmed !== plan.name) update.name = trimmed;
    if (weeksChanged) update.num_weeks = weeks;
    if (Object.keys(update).length === 0) onClose();
    else onSave(update);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <form onSubmit={handleSubmit} noValidate>
        <DialogTitle>{t("settings.title")}</DialogTitle>
        <DialogContent>
          <Stack spacing={2.5} sx={{ pt: 1 }}>
            <TextField
              label={t("settings.name")}
              value={name}
              onChange={(e) => setName(e.target.value)}
              slotProps={{ htmlInput: { maxLength: 100 } }}
              error={trimmed === ""}
              helperText={trimmed === "" ? t("settings.nameRequired") : undefined}
              autoFocus
              fullWidth
            />
            <TextField
              select
              label={t("settings.weeks")}
              value={weeks}
              onChange={(e) => setWeeks(Number(e.target.value))}
              helperText={
                weeksChanged && hasGeneratedWeeks
                  ? t("settings.weeksResets")
                  : t("settings.weeksHint")
              }
              fullWidth
            >
              {WEEK_OPTIONS.map((n) => (
                <MenuItem key={n} value={n}>
                  {t("settings.weeksOption", { count: n })}
                </MenuItem>
              ))}
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button onClick={onClose}>{t("actions.cancel")}</Button>
          <Button type="submit" variant="contained" disabled={trimmed === ""} loading={saving}>
            {t("actions.save")}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}