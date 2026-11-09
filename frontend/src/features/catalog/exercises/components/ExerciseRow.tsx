import { Box, Card, CardActionArea, Chip, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link as RouterLink, type To } from "react-router";

import { useLocalizedName } from "@/i18n/useLocalized.ts";
import type { ExerciseSummary } from "../../types.ts";
import { ExerciseThumbnail } from "./ExerciseThumbnail.tsx";

type ExerciseRowProps = {
  exercise: ExerciseSummary;
  to: To;
};

export function ExerciseRow({ exercise, to }: ExerciseRowProps) {
  const { t } = useTranslation("catalog");
  const localizedName = useLocalizedName();

  const equipment =
    exercise.equipment.length > 0
      ? exercise.equipment.map(localizedName).join(" · ")
      : t("exercise.bodyweight");

  return (
    <Card>
      <CardActionArea
        component={RouterLink}
        to={to}
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-start",
          gap: 2,
          p: 2,
        }}
      >
        <ExerciseThumbnail imageUrl={exercise.image_url} />

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography sx={{ fontWeight: 600, lineHeight: 1.3 }}>
            {localizedName(exercise)}
          </Typography>
          <Typography variant="body2" color="text.secondary" noWrap>
            {t(`muscleGroups.${exercise.main_group}`)} · {equipment}
          </Typography>
        </Box>

        <Stack direction="row" spacing={0.75} sx={{ flexShrink: 0 }}>
          {exercise.is_unilateral && (
            <Chip
              size="small"
              variant="outlined"
              label={t("exercise.unilateral")}
              sx={{ display: { xs: "none", sm: "inline-flex" } }}
            />
          )}
          <Chip
            size="small"
            sx={{ display: { xs: "none", sm: "inline-flex" } }}
            label={t(exercise.is_compound ? "exercise.compound" : "exercise.isolation")}
          />
        </Stack>
      </CardActionArea>
    </Card>
  );
}
