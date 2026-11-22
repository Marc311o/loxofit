import { useState, type FormEvent } from "react";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Stack,
  TextField,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import { errorMessage } from "@/lib/api";

type SavePlanDialogProps = {
  initialName: string;
  saving: boolean;
  error: unknown;
  onClose: () => void;
  onSave: (name: string) => void;
};

/** Name of the plan the generated base week is saved as. Mounted only while open. */
export function SavePlanDialog({
  initialName,
  saving,
  error,
  onClose,
  onSave,
}: SavePlanDialogProps) {
  const { t } = useTranslation(["generator", "plans"]);
  const [name, setName] = useState(initialName);
  const trimmed = name.trim();

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (trimmed) onSave(trimmed);
  };

  return (
    <Dialog open onClose={onClose} maxWidth="xs" fullWidth>
      <form onSubmit={handleSubmit} noValidate>
        <DialogTitle>{t("save.title")}</DialogTitle>
        <DialogContent>
          <Stack spacing={2}>
            <DialogContentText>{t("save.body")}</DialogContentText>
            <TextField
              label={t("save.name")}
              value={name}
              onChange={(e) => setName(e.target.value)}
              slotProps={{ htmlInput: { maxLength: 100 } }}
              error={trimmed === ""}
              helperText={trimmed === "" ? t("save.nameRequired") : undefined}
              autoFocus
              fullWidth
            />
            {error !== null && error !== undefined && (
              <Alert severity="error">{errorMessage(error)}</Alert>
            )}
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button onClick={onClose}>{t("plans:actions.cancel")}</Button>
          <Button type="submit" variant="contained" disabled={trimmed === ""} loading={saving}>
            {t("plans:actions.save")}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}