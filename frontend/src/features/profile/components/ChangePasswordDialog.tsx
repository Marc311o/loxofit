import { useState, type FormEvent } from "react";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import { useChangePassword } from "@/features/auth/api";
import { PasswordRules } from "@/features/auth/components/PasswordRules";
import { passwordRules } from "@/features/auth/validation";
import { errorMessage } from "@/lib/api";
import { toast } from "@/lib/toast";

/** Current password, the new one twice. Mounted only while open. */
export function ChangePasswordDialog({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation("profile");
  const change = useChangePassword();
  const [current, setCurrent] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [tried, setTried] = useState(false);

  const wrongCurrent = change.error?.code === "INCORRECT_PASSWORD";
  const rulesMet = passwordRules(password, confirm).every((rule) => rule.ok);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    setTried(true);
    if (!current || !rulesMet) return;
    change.mutate(
      { current_password: current, new_password: password },
      {
        onSuccess: () => {
          toast.success(t("account.passwordChanged"));
          onClose();
        },
      },
    );
  };

  return (
    <Dialog open onClose={onClose} maxWidth="xs" fullWidth>
      <form onSubmit={handleSubmit} noValidate>
        <DialogTitle>{t("account.changePassword")}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <TextField
              type="password"
              label={t("account.currentPassword")}
              autoComplete="current-password"
              value={current}
              onChange={(e) => {
                setCurrent(e.target.value);
                if (change.isError) change.reset();
              }}
              error={wrongCurrent || (tried && !current)}
              helperText={wrongCurrent ? t("account.incorrectPassword") : undefined}
              autoFocus
              fullWidth
            />
            <TextField
              type="password"
              label={t("account.newPassword")}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              fullWidth
            />
            <TextField
              type="password"
              label={t("account.confirmPassword")}
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              fullWidth
            />
            <PasswordRules password={password} confirm={confirm} showErrors={tried} />
            {change.isError && !wrongCurrent && (
              <Alert severity="error">{errorMessage(change.error)}</Alert>
            )}
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button onClick={onClose}>{t("actions.cancel")}</Button>
          <Button type="submit" variant="contained" loading={change.isPending}>
            {t("account.changePassword")}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
