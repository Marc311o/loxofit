import { Box, Card, Skeleton, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import type { ExerciseDetail } from "@/features/catalog/types";
import { useLocalizedName } from "@/i18n/useLocalized";
import { FONT_DISPLAY, FONT_MONO } from "@/styles/theme";
import { formatTempo, useWeekdayName } from "../format";
import { prescriptionFor } from "../prescription";
import type { PlanAssumptions, PlanWeek } from "../types";

type WeekViewProps = {
  week: PlanWeek;
  details: ReadonlyMap<number, ExerciseDetail>;
  minutes?: number[];
  assumptions?: PlanAssumptions;
};

/** A week of the plan, read-only: sessions with their exercises and sets. */
export function WeekView({ week, details, minutes, assumptions }: WeekViewProps) {
  const { t } = useTranslation("plans");
  const localizedName = useLocalizedName();
  const weekdayName = useWeekdayName();

  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: {
          xs: "1fr",
          sm: "repeat(2, minmax(0, 1fr))",
          lg: "repeat(3, minmax(0, 1fr))",
        },
        gap: 1.5,
      }}
    >
      {week.sessions.map((session, index) => {
        const time = minutes?.[index];
        const over = time !== undefined && time > session.max_minutes;
        return (
          <Card key={session.id} sx={{ p: 2 }}>
            <Stack direction="row" sx={{ justifyContent: "space-between", gap: 1, pb: 1 }}>
              <Stack sx={{ minWidth: 0 }}>
                <Typography sx={{ fontFamily: FONT_DISPLAY, fontWeight: 600 }} noWrap>
                  {session.name}
                </Typography>
                <Typography sx={{ fontFamily: FONT_MONO, fontSize: 11, color: "text.secondary" }}>
                  {session.weekday ? weekdayName(session.weekday).toUpperCase() : "—"}
                </Typography>
              </Stack>
              {time !== undefined && (
                <Typography
                  sx={{
                    fontFamily: FONT_MONO,
                    fontSize: 12,
                    color: over ? "warning.dark" : "text.secondary",
                  }}
                >
                  {t("session.minutes", { minutes: Math.round(time) })}
                </Typography>
              )}
            </Stack>
            <Stack component="ul" spacing={1} sx={{ m: 0, p: 0, listStyle: "none" }}>
              {session.exercises.map((exercise) => {
                const detail = details.get(exercise.exercise_id);
                const prescription =
                  detail && assumptions ? prescriptionFor(detail, assumptions) : undefined;
                return (
                  <Stack component="li" key={exercise.id} sx={{ minWidth: 0 }}>
                    <Typography variant="body2" noWrap sx={{ fontWeight: 500 }}>
                      {detail ? localizedName(detail) : <Skeleton width={120} />}
                    </Typography>
                    <Typography
                      sx={{ fontFamily: FONT_MONO, fontSize: 11, color: "text.secondary" }}
                    >
                      {[
                        t("week.sets", { count: exercise.sets }),
                        prescription &&
                          t("prescription.reps", {
                            min: prescription.repRange[0],
                            max: prescription.repRange[1],
                          }),
                        t("prescription.rir", { rir: week.rir }),
                        prescription &&
                          t("prescription.tempo", { tempo: formatTempo(prescription.tempo) }),
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </Typography>
                  </Stack>
                );
              })}
            </Stack>
          </Card>
        );
      })}
    </Box>
  );
}