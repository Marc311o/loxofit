import { Box, Button, Card, Chip, Skeleton, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router";

import { FONT_DISPLAY, FONT_MONO } from "@/styles/theme";
import { usePlanAnalysis } from "../api";
import { useWeekdayName } from "../format";
import { peakWeek, scorePercent } from "../insights";
import type { PlanDetail } from "../types";

function Stat({ value, label, color }: { value: string; label: string; color?: string }) {
  return (
    <Stack spacing={0.25}>
      <Typography sx={{ fontFamily: FONT_DISPLAY, fontSize: 26, fontWeight: 600, color }}>
        {value}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
    </Stack>
  );
}

export function ActivePlanCard({ plan }: { plan: PlanDetail }) {
  const { t } = useTranslation("plans");
  const weekdayName = useWeekdayName();
  const analysis = usePlanAnalysis(plan.id);
  const base = plan.weeks[0];
  const sessions = base?.sessions ?? [];
  const peak = analysis.data ? peakWeek(analysis.data) : undefined;

  return (
    <Card
      component="section"
      aria-labelledby="active-plan-title"
      sx={{ p: { xs: 2, md: 3 }, borderWidth: 2, borderColor: "primary.main" }}
    >
      <Stack spacing={2.5}>
        <Stack direction="row" sx={{ justifyContent: "space-between", flexWrap: "wrap", gap: 2 }}>
          <Stack spacing={0.75} sx={{ alignItems: "flex-start" }}>
            <Chip size="small" color="primary" label={t("status.active")} />
            <Typography id="active-plan-title" variant="h2">
              {plan.name}
            </Typography>
          </Stack>
          <Stack direction="row" spacing={3.5}>
            {analysis.data ? (
              <Stat
                value={`${scorePercent(analysis.data)}%`}
                label={t("score.label")}
                color="primary.main"
              />
            ) : (
              <Skeleton width={64} height={56} />
            )}
            <Stat value={String(plan.num_weeks)} label={t("list.weeks")} />
            <Stat value={String(sessions.length)} label={t("list.sessionsPerWeek")} />
          </Stack>
        </Stack>

        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: `repeat(${plan.weeks.length}, minmax(0, 1fr))`,
            gap: 1,
          }}
          aria-hidden
        >
          {plan.weeks.map((week) => (
            <Stack key={week.id} spacing={0.75}>
              <Box
                sx={{
                  height: 6,
                  borderRadius: 2,
                  bgcolor: week.is_deload ? "divider" : "primary.light",
                }}
              />
              <Typography sx={{ fontFamily: FONT_MONO, fontSize: 11, color: "text.secondary" }}>
                {week.is_deload
                  ? t("week.deloadShort")
                  : t("week.short", { number: week.week_number })}
              </Typography>
            </Stack>
          ))}
        </Box>

        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "repeat(2, minmax(0, 1fr))",
              md: "repeat(4, minmax(0, 1fr))",
            },
            gap: 1.25,
          }}
        >
          {sessions.map((session, index) => {
            const minutes = peak?.session_minutes[index];
            const over = minutes !== undefined && minutes > session.max_minutes;
            return (
              <Stack
                key={session.id}
                spacing={0.5}
                sx={{ bgcolor: "background.default", borderRadius: 2, p: 1.5 }}
              >
                <Typography sx={{ fontFamily: FONT_MONO, fontSize: 11, color: "text.secondary" }}>
                  {session.weekday ? weekdayName(session.weekday).toUpperCase() : "—"}
                </Typography>
                <Typography sx={{ fontWeight: 600 }}>{session.name}</Typography>
                {minutes !== undefined && (
                  <Typography
                    variant="caption"
                    sx={{ color: over ? "warning.dark" : "text.secondary" }}
                  >
                    {t("session.minutes", { minutes: Math.round(minutes) })}
                    {over && ` · ${t("session.over")}`}
                  </Typography>
                )}
              </Stack>
            );
          })}
        </Box>

        <Stack direction="row" spacing={1.25}>
          <Button variant="outlined" component={RouterLink} to={`/plans/${plan.id}`}>
            {t("actions.edit")}
          </Button>
          <Button
            component={RouterLink}
            to={`/plans/${plan.id}/analysis`}
            sx={{ bgcolor: "primary.light", color: "primary.dark" }}
          >
            {t("tabs.analysis")}
          </Button>
        </Stack>
      </Stack>
    </Card>
  );
}
