import { useEffect, useState } from "react";
import { Alert, Snackbar } from "@mui/material";

import { onToast, type Toast } from "@/lib/toast";

const DURATION_MS = {
  success: 3500,
  info: 4000,
  warning: 6000,
  error: 6000,
} as const;

export function ToastHost() {
  const [queue, setQueue] = useState<Toast[]>([]);
  const [open, setOpen] = useState(false);
  const current = queue[0];

  useEffect(() => onToast((item) => setQueue((q) => [...q, item])), []);

  useEffect(() => {
    if (current) setOpen(true);
  }, [current]);

  function handleClose(_: unknown, reason?: string) {
    if (reason === "clickaway") return;
    setOpen(false);
  }

  return (
    <Snackbar
      key={current?.id}
      open={open && Boolean(current)}
      autoHideDuration={current ? DURATION_MS[current.severity] : null}
      onClose={handleClose}
      anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      slotProps={{
        transition: { onExited: () => setQueue((q) => q.slice(1)) },
      }}
      // Above the bottom navigation on phones
      sx={{
        bottom: { xs: "calc(88px + env(safe-area-inset-bottom))", md: 24 },
      }}
    >
      {current && (
        <Alert
          severity={current.severity}
          variant="filled"
          onClose={() => setOpen(false)}
          sx={{ width: "100%", alignItems: "center" }}
        >
          {current.message}
        </Alert>
      )}
    </Snackbar>
  );
}
