import { Box, Card, Skeleton, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import type { ExerciseDetail } from "@/features/catalog/types";
import { SessionTimeBadge, type SessionTime } from "@/features/plan/components/SessionCard";
import { useWeekdayName } from "@/features/plan/format";
import { prescriptionFor } from "@/features/plan/prescription";
import type { PlanAssumptions } from "@/features/plan/types";
import { useLocalizedName } from "@/i18n/useLocalized";
import { FONT_DISPLAY, FONT_MONO } from "@/styles/theme";
import type { GeneratedSession } from "../types";

type GeneratedSessionCardProps = {
  session: GeneratedSession;
  details: ReadonlyMap<number, ExerciseDetail>;
  time: SessionTime | undefined;
  assumptions: PlanAssumptions | undefined;
};

/** One generated session, read-only: exercises in order with their sets in week 1. */
export function GeneratedSessionCard({
  session,
  details,
  time,
  assumptions,
}: GeneratedSessionCardProps) {
  const { t } = useTranslation(["generator", "plans", "catalog"]);
  const weekdayName = useWeekdayName();
  const localizedName = useLocalizedName();

  const meta = [
    t(`focus.${session.focus}`),
    session.weekday ? weekdayName(session.weekday) : t("plans:session.noWeekdayShort"),
    t("plans:session.limitShort", { minutes: session.max_minutes }),
  ]
    .join(" · ")
    .toUpperCase();

  return (
    <Card component="section" aria-label={session.name} sx={{ p: 2, minWidth: 0 }}>
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", pb: 1 }}>
        <Stack spacing={0.25} sx={{ flex: 1, minWidth: 0 }}>
          <Typography
            component="h3"
            noWrap
            sx={{ fontFamily: FONT_DISPLAY, fontSize: 18, fontWeight: 600 }}
          >
            {session.name}
          </Typography>
          <Typography sx={{ fontFamily: FONT_MONO, fontSize: 11, color: "text.secondary" }}>
            {meta}
          </Typography>
        </Stack>
        {time && <SessionTimeBadge time={time} limit={session.max_minutes} />}
      </Stack>
      <Box component="ol" sx={{ m: 0, p: 0, listStyle: "none" }}>
        {session.exercises.map((exercise) => {
          const detail = details.get(exercise.exercise_id);
          const prescription = detail && assumptions && prescriptionFor(detail, assumptions);
          return (
            <Stack
              component="li"
              key={exercise.exercise_id}
              direction="row"
              spacing={1.5}
              sx={{ alignItems: "center", py: 1, borderTop: 1, borderColor: "divider" }}
            >
              <Box sx={{ flex: 1, minWidth: 0 }}>
                {detail ? (
                  <>
                    <Typography noWrap sx={{ fontWeight: 500, fontSize: 14 }}>
                      {localizedName(detail)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" noWrap component="p">
                      {t(`catalog:muscleGroups.${detail.main_group}`)}
                      {prescription &&
                        ` · ${t("plans:prescription.reps", {
                          min: prescription.repRange[0],
                          max: prescription.repRange[1],
                        })}`}
                    </Typography>
                  </>
                ) : (
                  <>
                    <Skeleton width="70%" />
                    <Skeleton width="40%" />
                  </>
                )}
              </Box>
              <Typography
                sx={{ fontFamily: FONT_MONO, fontSize: 13, flexShrink: 0, color: "text.secondary" }}
              >
                {t("plans:week.sets", { count: exercise.sets })}
              </Typography>
            </Stack>
          );
        })}
      </Box>
    </Card>
  );
}