import { Button, Paper, Slide, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

type EquipmentSaveBarProps = {
  open: boolean;
  summary: string;
  saving: boolean;
  onDiscard: () => void;
  onSave: () => void;
};

/** Slides in above the phone navigation only while there are unsaved changes. */
export function EquipmentSaveBar({
  open,
  summary,
  saving,
  onDiscard,
  onSave,
}: EquipmentSaveBarProps) {
  const { t } = useTranslation("catalog");

  return (
    <Slide direction="up" in={open} mountOnEnter unmountOnExit>
      <Paper
        elevation={6}
        role="region"
        aria-label={t("equipment.unsaved")}
        sx={{
          position: "sticky",
          bottom: { xs: "calc(76px + env(safe-area-inset-bottom))", md: 24 },
          zIndex: 1,
          px: 2,
          py: 1.5,
          borderRadius: 2,
          border: 1,
          borderColor: "primary.main",
        }}
      >
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={1.5}
          sx={{ alignItems: { sm: "center" }, justifyContent: "space-between" }}
        >
          <Stack spacing={0.25}>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {t("equipment.unsaved")}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {summary}
            </Typography>
          </Stack>
          <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end" }}>
            <Button onClick={onDiscard} disabled={saving}>
              {t("equipment.discard")}
            </Button>
            <Button variant="contained" onClick={onSave} loading={saving}>
              {t("equipment.save")}
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Slide>
  );
}
