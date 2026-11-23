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

import { useDeleteAccount } from "@/features/auth/api";
import { errorMessage } from "@/lib/api";

/** Deleting the account for good, confirmed by the password. Mounted only while open. */
export function DeleteAccountDialog({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation("profile");
  const remove = useDeleteAccount();
  const [password, setPassword] = useState("");
  const wrong = remove.error?.code === "INCORRECT_PASSWORD";

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (password) remove.mutate(password);
  };

  return (
    <Dialog open onClose={onClose} maxWidth="xs" fullWidth>
      <form onSubmit={handleSubmit} noValidate>
        <DialogTitle>{t("account.deleteTitle")}</DialogTitle>
        <DialogContent>
          <Stack spacing={2}>
            <DialogContentText>{t("account.deleteBody")}</DialogContentText>
            <TextField
              type="password"
              label={t("account.currentPassword")}
              autoComplete="current-password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (remove.isError) remove.reset();
              }}
              error={wrong}
              helperText={wrong ? t("account.incorrectPassword") : undefined}
              autoFocus
              fullWidth
            />
            {remove.isError && !wrong && (
              <Alert severity="error">{errorMessage(remove.error)}</Alert>
            )}
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button onClick={onClose}>{t("actions.cancel")}</Button>
          <Button
            type="submit"
            variant="contained"
            color="error"
            disabled={!password}
            loading={remove.isPending}
          >
            {t("account.deleteConfirm")}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
