import { useState } from "react";
import { Alert, Button, Chip, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { EmptyState } from "@/components/EmptyState";
import { SegmentedControl } from "@/components/SegmentedControl";
import { toast } from "@/lib/toast";
import { useGenerateProgression, usePlanAnalysis } from "../api";
import { WeekView } from "../components/WeekView";
import { usePlanOutlet } from "../planOutlet";
import { useExerciseDetails } from "../useExerciseDetails";

/** Weeks 2..N as computed by the progression - read-only, edits go through the base week. */
export function WeeksPage() {
  const { t } = useTranslation("plans");
  const { plan } = usePlanOutlet();
  const generate = useGenerateProgression(plan.id);
  const analysis = usePlanAnalysis(plan.id);
  const { details } = useExerciseDetails(
    plan.weeks.flatMap((w) => w.sessions.flatMap((s) => s.exercises.map((e) => e.exercise_id))),
  );
  const [selected, setSelected] = useState(2);

  const base = plan.weeks[0];
  const baseHasExercises = base?.sessions.some((s) => s.exercises.length > 0) ?? false;

  if (plan.weeks.length < 2) {
    return (
      <EmptyState
        title={t("weeks.emptyTitle", { last: plan.num_weeks })}
        description={t(baseHasExercises ? "weeks.emptyBody" : "editor.addExercisesFirst")}
        action={
          plan.status !== "archived" && (
            <Button
              variant="contained"
              disabled={!baseHasExercises}
              loading={generate.isPending}
              onClick={() =>
                generate.mutate(undefined, {
                  onSuccess: () =>
                    toast.success(t("editor.weeksComputed", { last: plan.num_weeks })),
                })
              }
            >
              {t("actions.computeWeeks", { last: plan.num_weeks })}
            </Button>
          )
        }
      />
    );
  }

  const week = plan.weeks.find((w) => w.week_number === selected) ?? plan.weeks[1];
  const weekAnalysis = analysis.data?.weeks.find((w) => w.week_number === week.week_number);

  return (
    <Stack spacing={2}>
      <Typography variant="body2" color="text.secondary">
        {t("weeks.intro")}
      </Typography>
      <SegmentedControl
        label={t("weeks.pick")}
        value={week.week_number}
        onChange={setSelected}
        fullWidth
        options={plan.weeks.slice(1).map((w) => ({
          value: w.week_number,
          label: w.is_deload ? t("week.deloadShort") : t("week.short", { number: w.week_number }),
        }))}
      />
      <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
        <Typography variant="h6" component="h2">
          {t("weeks.title", { number: week.week_number })}
        </Typography>
        {week.is_deload && <Chip size="small" color="warning" label={t("weeks.deload")} />}
      </Stack>
      {week.is_deload && <Alert severity="info">{t("weeks.deloadHint")}</Alert>}
      <WeekView
        week={week}
        details={details}
        minutes={weekAnalysis?.session_minutes}
        assumptions={analysis.data?.assumptions}
      />
    </Stack>
  );
}