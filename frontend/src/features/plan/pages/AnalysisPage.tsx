import { useState } from "react";
import CheckCircleRounded from "@mui/icons-material/CheckCircleRounded";
import { Alert, Box, Card, Skeleton, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { InfoHint } from "@/components/InfoHint";
import { SegmentedControl } from "@/components/SegmentedControl";
import { useMuscles } from "@/features/catalog/muscles/api";
import { useFormatNumber, useLocalizedName } from "@/i18n/useLocalized";
import { FONT_DISPLAY, FONT_MONO } from "@/styles/theme";
import { usePlanAnalysis } from "../api";
import { IssueList } from "../components/IssueList";
import { LandmarkLegend, VolumeBar } from "../components/VolumeBar";
import { peakWeek, planIssues, scorePercent, zoneCounts } from "../insights";
import { usePlanOutlet } from "../planOutlet";
import type { PlanAnalysis, VolumeZone, WeekAnalysis } from "../types";
import { ZONE_COLOR } from "../zones";

const ZONES: VolumeZone[] = ["below_mev", "mev_mav", "mav_mrv", "above_mrv"];

/** The whole mesocycle: score breakdown, what to fix and one week at a time in detail. */
export function AnalysisPage() {
  const { t } = useTranslation("plans");
  const { plan } = usePlanOutlet();
  const analysis = usePlanAnalysis(plan.id);
  const sessions = plan.weeks[0]?.sessions ?? [];
  const [selected, setSelected] = useState<number | null>(null);

  if (analysis.isPending) {
    return (
      <Stack spacing={2}>
        <Skeleton variant="rounded" height={110} />
        <Skeleton variant="rounded" height={360} />
      </Stack>
    );
  }
  if (!analysis.data) {
    return <Alert severity="error">{t("analysis.loadError")}</Alert>;
  }
  const data = analysis.data;
  const issues = planIssues(
    data,
    sessions.map((s) => s.max_minutes),
  );
  const week =
    data.weeks.find((w) => w.week_number === selected) ?? peakWeek(data) ?? data.weeks[0];

  return (
    <Stack spacing={2.5}>
      {data.source === "projected" && <Alert severity="info">{t("analysis.projected")}</Alert>}
      <SummaryTiles analysis={data} />
      <Card sx={{ p: 2.5, borderColor: issues.length === 0 ? "primary.main" : undefined }}>
        <Typography variant="h6" component="h2" sx={{ pb: 1.5 }}>
          {t("analysis.issuesTitle")}
        </Typography>
        <IssueList issues={issues} sessionNames={sessions.map((s) => s.name)} />
      </Card>

      <Stack
        direction="row"
        useFlexGap
        sx={{ alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 1.5 }}
      >
        <Typography variant="h6" component="h2">
          {t("analysis.weekTitle", { number: week.week_number })}
        </Typography>
        <SegmentedControl
          label={t("weeks.pick")}
          value={week.week_number}
          onChange={setSelected}
          options={data.weeks.map((w) => ({
            value: w.week_number,
            label: w.is_deload
              ? t("week.deloadShort")
              : t("week.short", { number: w.week_number }),
          }))}
        />
      </Stack>
      <MuscleVolumes week={week} />
      <SessionTimes
        week={week}
        names={sessions.map((s) => s.name)}
        limits={sessions.map((s) => s.max_minutes)}
      />
    </Stack>
  );
}

type Tile = {
  label: string;
  value: string;
  hint: string;
  ok?: boolean;
};

function SummaryTiles({ analysis }: { analysis: PlanAnalysis }) {
  const { t } = useTranslation("plans");
  const formatNumber = useFormatNumber();
  const peak = peakWeek(analysis);
  const counts = peak ? zoneCounts(peak) : undefined;
  const tracked = peak?.muscles.filter((m) => m.priority > 0).length ?? 0;
  const outside = counts ? counts.below_mev + counts.above_mrv : 0;

  const tiles: Tile[] = [
    { label: t("score.label"), value: `${scorePercent(analysis)}%`, hint: t("score.hint") },
    {
      label: t("analysis.raw"),
      value: `${formatNumber(analysis.score, 1)} / ${formatNumber(analysis.max_score, 1)}`,
      hint: t("analysis.rawHint"),
    },
    {
      label: t("analysis.timePenalty"),
      value: analysis.time_penalty > 0 ? formatNumber(-analysis.time_penalty, 1) : "0",
      hint: t("analysis.timePenaltyHint"),
      ok: analysis.time_penalty === 0,
    },
    {
      label: t("analysis.outOfRange"),
      value: `${outside} / ${tracked}`,
      hint: t("analysis.outOfRangeHint"),
      ok: outside === 0,
    },
  ];

  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: { xs: "repeat(2, minmax(0, 1fr))", md: "repeat(4, minmax(0, 1fr))" },
        gap: 1.5,
      }}
    >
      {tiles.map((tile) => (
        <Card
          key={tile.label}
          sx={{
            p: 2,
            borderColor:
              tile.ok === undefined ? undefined : tile.ok ? "primary.main" : "warning.main",
          }}
        >
          <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
            <Typography sx={{ fontFamily: FONT_MONO, fontSize: 11, color: "text.secondary" }}>
              {tile.label.toUpperCase()}
            </Typography>
            <InfoHint text={tile.hint} />
            {tile.ok && (
              <CheckCircleRounded
                fontSize="small"
                color="primary"
                titleAccess={t("analysis.ok")}
                sx={{ ml: "auto" }}
              />
            )}
          </Stack>
          <Typography
            sx={{ fontFamily: FONT_DISPLAY, fontSize: { xs: 22, sm: 28 }, fontWeight: 600 }}
          >
            {tile.value}
          </Typography>
        </Card>
      ))}
    </Box>
  );
}

/** Sets per muscle in one week, against its landmarks. */
function MuscleVolumes({ week }: { week: WeekAnalysis }) {
  const { t } = useTranslation("plans");
  const muscles = useMuscles();
  const localizedName = useLocalizedName();
  const formatNumber = useFormatNumber();

  const rows = week.muscles.filter((m) => m.priority > 0);
  const scale = Math.max(...rows.map((m) => Math.max(m.mrv * 1.2, m.volume)), 1);

  return (
    <Card sx={{ p: 2.5 }}>
      <Stack
        direction="row"
        useFlexGap
        sx={{ justifyContent: "space-between", flexWrap: "wrap", gap: 1.5, pb: 2 }}
      >
        <Typography variant="body2" color="text.secondary">
          {week.is_deload
            ? t("analysis.deloadNote")
            : t("analysis.weekScore", { score: formatNumber(week.volume_score, 1) })}
        </Typography>
        <Stack
          direction="row"
          useFlexGap
          sx={{ flexWrap: "wrap", columnGap: 1.5, rowGap: 0.5, alignItems: "center" }}
        >
          {ZONES.map((zone) => (
            <Stack key={zone} direction="row" spacing={0.75} sx={{ alignItems: "center" }}>
              <Box sx={{ width: 10, height: 10, borderRadius: 0.5, bgcolor: ZONE_COLOR[zone] }} />
              <Typography variant="caption">{t(`zones.${zone}`)}</Typography>
            </Stack>
          ))}
        </Stack>
      </Stack>
      <Stack
        component="ul"
        spacing={1.25}
        aria-label={t("panel.volumeLabel")}
        sx={{ m: 0, p: 0, listStyle: "none" }}
      >
        {rows.map((m) => {
          const muscle = muscles.data?.find((x) => x.id === m.muscle_id);
          const name = muscle ? localizedName(muscle) : m.muscle_code;
          return (
            <Box
              component="li"
              key={m.muscle_id}
              aria-label={`${name}: ${t("analysis.cellHint", {
                sets: formatNumber(m.volume, 1),
                mev: formatNumber(m.mev, 0),
                mav: formatNumber(m.mav_upper, 0),
                mrv: formatNumber(m.mrv, 0),
              })}`}
              sx={{
                display: "grid",
                gridTemplateColumns: {
                  xs: "minmax(0, 1.3fr) minmax(0, 1fr) 36px",
                  md: "200px minmax(0, 1fr) 48px 170px",
                },
                alignItems: "center",
                gap: 1.5,
              }}
            >
              <Typography noWrap variant="body2" title={name}>
                {name}
              </Typography>
              <VolumeBar
                tone="light"
                volume={m.volume}
                mev={m.mev}
                mav={m.mav_upper}
                mrv={m.mrv}
                scale={scale}
                color={ZONE_COLOR[m.zone]}
              />
              <Typography sx={{ fontFamily: FONT_MONO, fontSize: 12, textAlign: "right" }}>
                {formatNumber(m.volume, 1)}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  display: { xs: "none", md: "block" },
                  color: m.zone === "above_mrv" ? "warning.dark" : "text.secondary",
                }}
              >
                {t(`zones.${m.zone}`)}
                {m.volume - m.effective_volume > 0.05 &&
                ` · ${t("analysis.effective", { sets: formatNumber(m.effective_volume, 1) })}`}
              </Typography>
            </Box>
          );
        })}
      </Stack>
      <Box sx={{ pt: 2 }}>
        <LandmarkLegend tone="light" />
      </Box>
    </Card>
  );
}

function SessionTimes({
  week,
  names,
  limits,
}: {
  week: WeekAnalysis;
  names: string[];
  limits: number[];
}) {
  const { t } = useTranslation("plans");
  if (names.length === 0) return null;
  const allWithin = names.every((_, i) => (week.session_minutes[i] ?? 0) <= limits[i]);

  return (
    <Card sx={{ p: 2.5, borderColor: allWithin ? "primary.main" : "warning.main" }}>
      <Typography variant="h6" component="h2" sx={{ pb: 1.5 }}>
        {t("analysis.timesTitle", { number: week.week_number })}
      </Typography>
      <Stack component="ul" spacing={1.25} sx={{ m: 0, p: 0, listStyle: "none" }}>
        {names.map((name, i) => {
          const minutes = week.session_minutes[i] ?? 0;
          const limit = limits[i];
          const over = minutes > limit;
          return (
            <Box
              component="li"
              key={`${name}-${i}`}
              sx={{
                display: "grid",
                gridTemplateColumns: "120px minmax(0, 1fr) 90px",
                gap: 1.5,
                alignItems: "center",
              }}
            >
              <Typography noWrap variant="body2">
                {name}
              </Typography>
              <Box
                sx={{ position: "relative", height: 8, borderRadius: 0.5, bgcolor: "action.hover" }}
              >
                <Box
                  sx={{
                    position: "absolute",
                    top: 0,
                    bottom: 0,
                    left: 0,
                    width: `${Math.min(100, (minutes / Math.max(limit, minutes)) * 100)}%`,
                    borderRadius: 0.5,
                    bgcolor: over ? ZONE_COLOR.above_mrv : ZONE_COLOR.mev_mav,
                  }}
                />
              </Box>
              <Typography
                variant="body2"
                sx={{
                  fontFamily: FONT_MONO,
                  fontSize: 12,
                  textAlign: "right",
                  color: over ? "warning.dark" : "text.secondary",
                }}
              >
                {t("analysis.minutesOf", { minutes: Math.round(minutes), limit })}
              </Typography>
            </Box>
          );
        })}
      </Stack>
    </Card>
  );
}