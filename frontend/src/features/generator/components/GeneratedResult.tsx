import { useState } from "react";
import CasinoOutlined from "@mui/icons-material/CasinoOutlined";
import { Box, Button, Card, Stack, Tooltip, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";

import { InfoHint } from "@/components/InfoHint";
import { AnalysisPanel } from "@/features/plan/components/AnalysisPanel";
import type { SessionTime } from "@/features/plan/components/SessionCard";
import { peakWeek } from "@/features/plan/insights";
import { useExerciseDetails } from "@/features/plan/useExerciseDetails";
import { useFormatNumber } from "@/i18n/useLocalized";
import { toast } from "@/lib/toast";
import { FONT_MONO } from "@/styles/theme";
import { useGenerationAnalysis, useSaveGeneratedPlan } from "../api";
import { historyPoints } from "../score";
import type { GenerationRun } from "../types";
import { ConvergenceChart } from "./ConvergenceChart";
import { GeneratedSessionCard } from "./GeneratedSessionCard";
import { SavePlanDialog } from "./SavePlanDialog";

type GeneratedResultProps = {
  /** A finished run - `sessions`, `history` and `max_score` are set. */
  run: GenerationRun;
  onAnother: () => void;
  anotherPending: boolean;
};

/** The generated plan: its sessions, the analysis with the score and the search behind it. */
export function GeneratedResult({ run, onAnother, anotherPending }: GeneratedResultProps) {
  const { t } = useTranslation(["generator", "plans"]);
  const navigate = useNavigate();
  const formatNumber = useFormatNumber();
  const [saving, setSaving] = useState(false);
  const analysis = useGenerationAnalysis(run.id, { enabled: true });
  const save = useSaveGeneratedPlan(run.id);

  const sessions = run.sessions ?? [];
  const { details } = useExerciseDetails(
    sessions.flatMap((s) => s.exercises.map((e) => e.exercise_id)),
  );

  const first = analysis.data?.weeks[0];
  const peak = analysis.data ? peakWeek(analysis.data) : undefined;
  const timeOf = (index: number): SessionTime | undefined =>
    first && peak
      ? {
          base: first.session_minutes[index],
          peak: peak.session_minutes[index],
          peakWeek: peak.week_number,
        }
      : undefined;

  const seconds =
    run.started_at && run.finished_at
      ? (Date.parse(run.finished_at) - Date.parse(run.started_at)) / 1000
      : null;

  const handleSave = (name: string) =>
    save.mutate(name, {
      onSuccess: (plan) => {
        toast.success(t("save.saved"));
        navigate(`/plans/${plan.id}`);
      },
    });

  return (
    <Stack spacing={2.5} sx={{ minWidth: 0 }}>
      <Stack
        direction="row"
        sx={{ justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: 1.5 }}
      >
        <Stack spacing={0.25}>
          <Typography variant="h2">{t("result.title")}</Typography>
          {run.evaluations !== null && seconds !== null && (
            <Typography sx={{ fontFamily: FONT_MONO, fontSize: 12, color: "text.secondary" }}>
              {t("result.meta", {
                evaluations: formatNumber(run.evaluations),
                seconds: formatNumber(seconds, 1),
              })}
            </Typography>
          )}
        </Stack>
        <Tooltip title={t("result.anotherHint")}>
          <Button
            variant="outlined"
            startIcon={<CasinoOutlined />}
            onClick={onAnother}
            loading={anotherPending}
          >
            {t("result.another")}
          </Button>
        </Tooltip>
      </Stack>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", md: "minmax(0, 1fr) 320px" },
          gap: 2.5,
          alignItems: "start",
        }}
      >
        <Box sx={{ order: { xs: 1, md: 2 }, position: { md: "sticky" }, top: { md: 24 } }}>
          <AnalysisPanel
            analysis={analysis.data}
            updating={false}
            sessionNames={sessions.map((s) => s.name)}
            sessionLimits={sessions.map((s) => s.max_minutes)}
            action={
              run.plan_id
                ? {
                    label: t("result.open"),
                    onClick: () => navigate(`/plans/${run.plan_id}`),
                  }
                : { label: t("result.save"), onClick: () => setSaving(true) }
            }
          />
        </Box>

        <Stack
          spacing={2}
          aria-label={t("result.sessionsLabel")}
          sx={{ order: { xs: 2, md: 1 }, minWidth: 0 }}
        >
          {sessions.map((session, i) => (
            <GeneratedSessionCard
              key={i}
              session={session}
              details={details}
              time={timeOf(i)}
              assumptions={analysis.data?.assumptions}
            />
          ))}
          {run.history && run.max_score !== null && run.evaluations !== null && (
            <Card component="section" sx={{ p: 2 }}>
              <Stack direction="row" spacing={0.5} sx={{ alignItems: "center", mb: 1 }}>
                <Typography variant="overline" color="text.secondary" component="h3">
                  {t("chart.title")}
                </Typography>
                <InfoHint text={t("chart.hint")} />
              </Stack>
              <ConvergenceChart
                points={historyPoints(run.history, run.max_score)}
                budget={run.budget}
                until={run.evaluations}
                height={140}
              />
            </Card>
          )}
        </Stack>
      </Box>

      {saving && (
        <SavePlanDialog
          initialName={t("save.defaultName", {
            template: t(`templates.${run.request.template}.label`),
          })}
          saving={save.isPending}
          error={save.error}
          onClose={() => {
            setSaving(false);
            save.reset();
          }}
          onSave={handleSave}
        />
      )}
    </Stack>
  );
}
