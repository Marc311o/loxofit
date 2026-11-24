import type { ReactNode } from "react";
import { Box, Chip, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { DotScale } from "@/components/DotScale.tsx";
import { InfoHint } from "@/components/InfoHint.tsx";
import { useLanguage } from "@/i18n";
import { useLocalizedName } from "@/i18n/useLocalized.ts";
import { FONT_MONO } from "@/styles/theme.ts";
import type { ExerciseDetail } from "../../types.ts";
import { ExerciseThumbnail } from "./ExerciseThumbnail.tsx";
import { MuscleShareList } from "./MuscleShareList.tsx";

type FactProps = {
  label: string;
  hint?: string;
  children: ReactNode;
};

function Fact({ label, hint, children }: FactProps) {
  return (
    <Stack spacing={0.75} sx={{ p: 1.75, borderRadius: 2, bgcolor: "background.default" }}>
      <Stack direction="row" sx={{ alignItems: "center", minHeight: 24 }}>
        <Typography variant="overline" color="text.secondary" component="p">
          {label}
        </Typography>
        {hint && <InfoHint text={hint} />}
      </Stack>
      {children}
    </Stack>
  );
}

function instructionSteps(text: string | null): string[] {
  return (text ?? "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

export function ExerciseDetailContent({ exercise }: { exercise: ExerciseDetail }) {
  const { t } = useTranslation("catalog");
  const language = useLanguage();
  const localizedName = useLocalizedName();

  // The other language's name helps users who know the exercise by it.
  const otherName = language === "pl" ? exercise.name_en : exercise.name_pl;
  const [ownInstructions, otherInstructions] =
    language === "pl"
      ? [exercise.instructions_pl, exercise.instructions_en]
      : [exercise.instructions_en, exercise.instructions_pl];
  const steps = instructionSteps(ownInstructions ?? otherInstructions);

  return (
    <Stack spacing={3.5}>
      <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
        <ExerciseThumbnail imageUrl={exercise.image_url} size={72} />
        <Stack spacing={0.5} sx={{ minWidth: 0 }}>
          <Typography variant="overline" color="text.secondary">
            {t(`muscleGroups.${exercise.main_group}`)} ·{" "}
            {t(exercise.is_compound ? "exercise.compound" : "exercise.isolation")}
          </Typography>
          <Typography variant="h2" id="exercise-title">
            {localizedName(exercise)}
          </Typography>
          <Typography color="text.secondary">{otherName}</Typography>
        </Stack>
      </Stack>

      <Stack direction="row" spacing={0.75} useFlexGap sx={{ flexWrap: "wrap" }}>
        {exercise.equipment.length > 0 ? (
          exercise.equipment.map((item) => <Chip key={item.id} label={localizedName(item)} />)
        ) : (
          <Chip label={t("exercise.bodyweight")} />
        )}
      </Stack>

      <Box component="section" aria-labelledby="muscles-heading">
        <Stack direction="row" sx={{ alignItems: "center", mb: 2 }}>
          <Typography variant="h3" id="muscles-heading">
            {t("exercise.musclesWorked")}
          </Typography>
          <InfoHint text={t("exercise.musclesHint")} />
        </Stack>
        <MuscleShareList muscles={exercise.muscles} />
      </Box>

      <Box
        component="section"
        aria-label={t("exercise.facts")}
        sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1.25 }}
      >
        <Fact label={t("exercise.pattern")}>
          <Typography sx={{ fontWeight: 600 }}>
            {t(`patterns.${exercise.movement_pattern}`)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t(exercise.is_unilateral ? "exercise.unilateral" : "exercise.bilateral")}
          </Typography>
        </Fact>
        <Fact
          label={t("exercise.tempo")}
          hint={exercise.default_tempo ? t("exercise.tempoHint") : undefined}
        >
          <Typography sx={{ fontWeight: 600, fontFamily: FONT_MONO }}>
            {exercise.default_tempo ?? "—"}
          </Typography>
        </Fact>
        <Fact label={t("exercise.fatigue")} hint={t("exercise.fatigueHint")}>
          <DotScale
            value={exercise.fatigue_cost}
            label={t("exercise.outOfFive", { value: exercise.fatigue_cost })}
          />
        </Fact>
        <Fact label={t("exercise.complexity")} hint={t("exercise.complexityHint")}>
          <DotScale
            value={exercise.complexity}
            label={t("exercise.outOfFive", { value: exercise.complexity })}
          />
        </Fact>
      </Box>

      {steps.length > 0 && (
        <Box component="section" aria-labelledby="instructions-heading">
          <Typography variant="h3" id="instructions-heading" sx={{ mb: 1 }}>
            {t("exercise.howTo")}
          </Typography>
          <Box
            component="ol"
            sx={{
              m: 0,
              pl: 3,
              display: "grid",
              gap: 1,
              "& li::marker": { fontFamily: FONT_MONO },
            }}
          >
            {steps.map((step) => (
              <Typography component="li" key={step}>
                {step}
              </Typography>
            ))}
          </Box>
        </Box>
      )}
    </Stack>
  );
}
