import { Box, Button, Skeleton, Stack, Tooltip, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { InfoHint } from "@/components/InfoHint";
import { useMuscles } from "@/features/catalog/muscles/api";
import { useFormatNumber, useLocalizedName } from "@/i18n/useLocalized";
import { FONT_DISPLAY, FONT_MONO } from "@/styles/theme";
import { peakWeek, planIssues, scorePercent, zoneCounts } from "../insights";
import type { PlanAnalysis } from "../types";
import { ZONE_COLOR } from "../zones";
import { IssueList } from "./IssueList";
import { LandmarkLegend, VolumeBar } from "./VolumeBar";

type AnalysisPanelProps = {
  analysis: PlanAnalysis | undefined;
  updating: boolean;
  sessionNames: string[];
  sessionLimits: number[];
  numWeeks: number;
  canGenerate: boolean;
  generateHint: string;
  generating: boolean;
  onGenerate: () => void;
};

/** Live feedback next to the editor: score, what to fix and volume per muscle at the peak week. */
export function AnalysisPanel({
  analysis,
  updating,
  sessionNames,
  sessionLimits,
  numWeeks,
  canGenerate,
  generateHint,
  generating,
  onGenerate,
}: AnalysisPanelProps) {
  const { t } = useTranslation("plans");
  const muscles = useMuscles();
  const localizedName = useLocalizedName();
  const formatNumber = useFormatNumber();

  const peak = analysis ? peakWeek(analysis) : undefined;
  const counts = peak ? zoneCounts(peak) : undefined;
  const tracked = peak?.muscles.filter((m) => m.priority > 0) ?? [];
  const scale = Math.max(...tracked.map((m) => Math.max(m.mrv * 1.2, m.volume)), 1);

  return (
    <Box
      component="aside"
      aria-label={t("panel.label")}
      aria-busy={updating}
      sx={{
        bgcolor: "primary.dark",
        color: "#F3F4F1",
        borderRadius: 2,
        p: 2.5,
        display: "flex",
        flexDirection: "column",
        gap: 2,
      }}
    >
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "flex-end" }}>
        <Stack spacing={0.25}>
          <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
            <Typography
              sx={{
                fontFamily: FONT_MONO,
                fontSize: 11,
                letterSpacing: "0.08em",
                color: "#A9CFC4",
              }}
            >
              {t("score.label").toUpperCase()}
            </Typography>
            <Box sx={{ "& .MuiIconButton-root": { color: "#A9CFC4" } }}>
              <InfoHint text={t("score.hint")} />
            </Box>
          </Stack>
          {analysis ? (
            <Typography
              sx={{
                fontFamily: FONT_DISPLAY,
                fontSize: 40,
                fontWeight: 600,
                lineHeight: 1.1,
                opacity: updating ? 0.6 : 1,
                transition: "opacity 150ms",
              }}
            >
              {scorePercent(analysis)}%
            </Typography>
          ) : (
            <Skeleton width={96} height={52} sx={{ bgcolor: "rgba(255,255,255,0.12)" }} />
          )}
        </Stack>
        {peak && (
          <Typography sx={{ fontFamily: FONT_MONO, fontSize: 11, color: "#A9CFC4", pb: 1 }}>
            {t("panel.peakWeek", { number: peak.week_number }).toUpperCase()}
          </Typography>
        )}
      </Stack>

      {analysis?.source === "projected" && (
        <Typography variant="caption" sx={{ color: "#A9CFC4", mt: -1 }}>
          {t("panel.projected")}
        </Typography>
      )}

      {counts && (
        <Typography variant="body2" sx={{ color: "#E4F1EC" }}>
          {t("panel.inRange", {
            count: counts.mev_mav + counts.mav_mrv,
            total: tracked.length,
          })}
        </Typography>
      )}

      {analysis && (
        <IssueList
          issues={planIssues(analysis, sessionLimits)}
          sessionNames={sessionNames}
          inverted
          limit={4}
        />
      )}

      {peak && (
        <Stack
          component="ul"
          spacing={1.1}
          aria-label={t("panel.volumeLabel")}
          sx={{ m: 0, p: 0, pt: 1.5, listStyle: "none", borderTop: "1px solid #2A5A52" }}
        >
          {tracked.map((m) => {
            const muscle = muscles.data?.find((x) => x.id === m.muscle_id);
            return (
              <Box
                component="li"
                key={m.muscle_id}
                sx={{
                  display: "grid",
                  gridTemplateColumns: "minmax(0, 1.2fr) minmax(0, 1fr) 32px",
                  alignItems: "center",
                  gap: 1.25,
                }}
              >
                <Typography
                  noWrap
                  title={muscle ? localizedName(muscle) : m.muscle_code}
                  sx={{ fontSize: 12, color: "#CFE3DC" }}
                >
                  {muscle ? localizedName(muscle) : m.muscle_code}
                </Typography>
                <VolumeBar
                  volume={m.volume}
                  mev={m.mev}
                  mav={m.mav_upper}
                  mrv={m.mrv}
                  scale={scale}
                  color={m.zone === "mav_mrv" ? "#7FC2AE" : ZONE_COLOR[m.zone]}
                />
                <Typography sx={{ fontFamily: FONT_MONO, fontSize: 11, textAlign: "right" }}>
                  {formatNumber(m.volume, 1)}
                </Typography>
              </Box>
            );
          })}
        </Stack>
      )}
      {peak && <LandmarkLegend />}

      <Tooltip title={canGenerate ? "" : generateHint}>
        <span>
          <Button
            fullWidth
            size="large"
            disabled={!canGenerate}
            loading={generating}
            onClick={onGenerate}
            sx={{
              bgcolor: "#F3F4F1",
              color: "primary.dark",
              "&:hover": { bgcolor: "#FFFFFF" },
              "&.Mui-disabled": { bgcolor: "rgba(243,244,241,0.3)", color: "rgba(18,64,58,0.6)" },
            }}
          >
            {t("actions.computeWeeks", { last: numWeeks })}
          </Button>
        </span>
      </Tooltip>
    </Box>
  );
}