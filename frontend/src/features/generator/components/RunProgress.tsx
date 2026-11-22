import { useState } from "react";
import { Card, LinearProgress, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { useFormatNumber } from "@/i18n/useLocalized";
import { FONT_DISPLAY, FONT_MONO } from "@/styles/theme";
import { scorePct } from "../score";
import type { GenerationRun } from "../types";
import { ConvergenceChart, type ConvergencePoint } from "./ConvergenceChart";

/**
 * A run in progress: how much of the budget is spent and the best score so far,
 * drawn as it improves. Mount with `key={run.id}` - the points belong to one run.
 */
export function RunProgress({ run }: { run: GenerationRun }) {
  const { t } = useTranslation("generator");
  const formatNumber = useFormatNumber();
  const progress = run.progress;
  const evaluations = progress?.evaluations ?? 0;
  const best = progress?.best_score ?? null;
  const pct = best !== null && run.max_score ? scorePct(best, run.max_score) : null;

  // The best score is only seen at every poll, so the line is built from the polls.
  const [points, setPoints] = useState<ConvergencePoint[]>([]);
  const [seen, setSeen] = useState(-1);
  if (evaluations !== seen) {
    setSeen(evaluations);
    if (pct !== null && pct !== points.at(-1)?.[1]) setPoints([...points, [evaluations, pct]]);
  }

  const queued = run.status === "queued" || evaluations === 0;

  return (
    <Card component="section" aria-label={t("progress.label")} aria-busy sx={{ p: 2.5 }}>
      <Stack spacing={2}>
        <Stack
          direction="row"
          sx={{ justifyContent: "space-between", alignItems: "flex-end", gap: 2 }}
        >
          <Stack spacing={0.5}>
            <Typography variant="h3" component="h2">
              {queued ? t("progress.queued") : t("progress.running")}
            </Typography>
            <Typography sx={{ fontFamily: FONT_MONO, fontSize: 12, color: "text.secondary" }}>
              {t("progress.evaluations", {
                done: formatNumber(evaluations),
                budget: formatNumber(run.budget),
              })}
            </Typography>
          </Stack>
          {pct !== null && (
            <Stack sx={{ alignItems: "flex-end" }}>
              <Typography variant="overline" color="text.secondary">
                {t("progress.best")}
              </Typography>
              <Typography
                sx={{ fontFamily: FONT_DISPLAY, fontSize: 32, fontWeight: 600, lineHeight: 1 }}
              >
                {Math.round(pct)}%
              </Typography>
            </Stack>
          )}
        </Stack>
        <LinearProgress
          variant={queued ? "indeterminate" : "determinate"}
          value={(evaluations / run.budget) * 100}
          aria-label={t("progress.label")}
          sx={{ height: 6, borderRadius: 3 }}
        />
        <ConvergenceChart points={points} budget={run.budget} until={evaluations} />
      </Stack>
    </Card>
  );
}