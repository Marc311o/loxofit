import { useEffect, useState } from "react";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from "@mui/material";
import { useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router";

import { onSessionExpired } from "@/lib/session";

export function SessionExpiredDialog() {
  const { t } = useTranslation("auth");
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => onSessionExpired(() => setOpen(true)), []);

  function handleSignIn() {
    setOpen(false);
    queryClient.clear();
    navigate("/login", { replace: true, state: { from: location.pathname } });
  }

  return (
    <Dialog open={open} aria-labelledby="session-expired-title">
      <DialogTitle id="session-expired-title">{t("sessionExpired.title")}</DialogTitle>
      <DialogContent>
        <DialogContentText>{t("sessionExpired.body")}</DialogContentText>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button variant="contained" onClick={handleSignIn}>
          {t("sessionExpired.action")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
