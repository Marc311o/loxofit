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
import { useLocation, useNavigate } from "react-router";

import { onSessionExpired } from "@/lib/session";

export function SessionExpiredDialog() {
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
      <DialogTitle id="session-expired-title">Session expired</DialogTitle>
      <DialogContent>
        <DialogContentText>
          You have been signed out. Log in again to continue.
        </DialogContentText>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button variant="contained" onClick={handleSignIn}>
          Log in again
        </Button>
      </DialogActions>
    </Dialog>
  );
}
