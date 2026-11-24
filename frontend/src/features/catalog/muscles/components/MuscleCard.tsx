import ArrowForwardRounded from "@mui/icons-material/ArrowForwardRounded";
import { Box, Button, Card, Chip, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router";

import { InfoHint } from "@/components/InfoHint";
import { useLanguage } from "@/i18n";
import { useLocalizedName } from "@/i18n/useLocalized";
import { MuscleFigure } from "../../components/MuscleFigure";
import type { Muscle } from "../../types";

export function MuscleCard({ muscle }: { muscle: Muscle }) {
  const { t } = useTranslation("catalog");
  const language = useLanguage();
  const localizedName = useLocalizedName();
  const otherName = language === "pl" ? muscle.name_en : muscle.name_pl;

  return (
    <Card sx={{ p: 2 }}>
      <Stack
        direction="row"
        spacing={2}
        sx={{ alignItems: "center", justifyContent: "space-between" }}
      >
        <MuscleFigure code={muscle.code} />
        <Box sx={{ minWidth: 0, flex: 1 }}>
          <Typography sx={{ fontWeight: 600, lineHeight: 1.3 }}>{localizedName(muscle)}</Typography>
          <Typography variant="body2" color="text.secondary">
            {otherName}
          </Typography>
          {!muscle.is_volume_target && (
            <Stack direction="row" sx={{ alignItems: "center", mt: 1 }}>
              <Chip size="small" variant="outlined" label={t("muscles.notTracked")} />
              <InfoHint text={t("muscles.notTrackedHint")} />
            </Stack>
          )}
        </Box>
        <Button
          size="small"
          component={RouterLink}
          to={`/catalog/exercises?muscle=${muscle.id}`}
          endIcon={<ArrowForwardRounded />}
          sx={{ flexShrink: 0 }}
        >
          {t("muscles.showExercises")}
        </Button>
      </Stack>
    </Card>
  );
}
