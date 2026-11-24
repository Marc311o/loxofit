import { useMemo, useRef, useState } from "react";
import ArrowBackRounded from "@mui/icons-material/ArrowBackRounded";
import AutoAwesomeRounded from "@mui/icons-material/AutoAwesomeRounded";
import { Alert, Box, Button, Skeleton, Stack } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link as RouterLink, useSearchParams } from "react-router";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { useMyProfile } from "@/features/profile/api";
import { errorMessage } from "@/lib/api";
import { isActive, useGenerationRun, useStartGeneration } from "../api";
import { GeneratedResult } from "../components/GeneratedResult";
import { GeneratorFormCard } from "../components/GeneratorFormCard";
import { RunProgress } from "../components/RunProgress";
import {
  focuses,
  focusLetters,
  fromRequest,
  type GeneratorForm,
  initialForm,
  toRequest,
} from "../request";
import type { GenerationRequest } from "../types";

/** The run on screen lives in the URL (?run=<id>), so a reload or a shared link keeps it. */
const RUN_PARAM = "run";

export function GeneratorPage() {
  const { t } = useTranslation(["generator", "common"]);
  const [params, setParams] = useSearchParams();
  const runId = params.get(RUN_PARAM);
  const run = useGenerationRun(runId);
  const profile = useMyProfile();
  const start = useStartGeneration();
  const resultRef = useRef<HTMLDivElement>(null);

  // Until the user edits it, the form shows the run on screen, else the profile's defaults.
  const [edited, setEdited] = useState<GeneratorForm | null>(null);
  const request = run.data?.request;
  const profileReady = !profile.isPending;
  const fallback = useMemo(
    () => (request ? fromRequest(request) : profileReady ? initialForm(profile.data) : null),
    [request, profileReady, profile.data],
  );
  const form = edited ?? fallback;

  const sessionFocuses = form ? focuses(form) : [];
  const letters = focusLetters(sessionFocuses);
  const names = sessionFocuses.map((f, i) =>
    letters[i] ? `${t(`focus.${f}`)} ${letters[i]}` : t(`focus.${f}`),
  );

  const startRun = (body: GenerationRequest) =>
    start.mutate(body, {
      onSuccess: (started) => {
        setParams({ [RUN_PARAM]: started.id });
        // On narrow screens the result is below the form - bring it into view.
        if (window.matchMedia("(max-width: 1199.95px)").matches) {
          resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      },
    });

  const header = (
    <PageHeader
      title={t("title")}
      subtitle={t("intro")}
      actions={
        <Button component={RouterLink} to="/plans" startIcon={<ArrowBackRounded />}>
          {t("back")}
        </Button>
      }
    />
  );

  return (
    <>
      {header}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", lg: "340px minmax(0, 1fr)" },
          gap: 3,
          alignItems: "start",
        }}
      >
        <Box sx={{ position: { lg: "sticky" }, top: { lg: 24 } }}>
          {form ? (
            <GeneratorFormCard
              form={form}
              names={names}
              onChange={setEdited}
              onSubmit={() => startRun(toRequest(form, names))}
              submitting={start.isPending}
              error={start.error}
            />
          ) : (
            <Skeleton variant="rounded" height={560} sx={{ borderRadius: 2 }} />
          )}
        </Box>

        <Box ref={resultRef} sx={{ minWidth: 0, scrollMarginTop: 16 }}>
          {runId === null ? (
            <EmptyState
              icon={<AutoAwesomeRounded />}
              title={t("placeholder.title")}
              description={t("placeholder.body")}
            />
          ) : run.isError ? (
            <EmptyState
              title={t("result.loadError")}
              description={errorMessage(run.error)}
              action={
                <Button onClick={() => void run.refetch()}>{t("common:actions.tryAgain")}</Button>
              }
            />
          ) : !run.data ? (
            <Skeleton variant="rounded" height={320} sx={{ borderRadius: 2 }} />
          ) : isActive(run.data) ? (
            <RunProgress key={run.data.id} run={run.data} />
          ) : run.data.status === "failed" ? (
            <Stack spacing={2}>
              <Alert
                severity="error"
                action={
                  <Button
                    color="inherit"
                    size="small"
                    loading={start.isPending}
                    onClick={() => startRun({ ...run.data.request, seed: null })}
                  >
                    {t("result.retry")}
                  </Button>
                }
              >
                {t("result.failed")}
              </Alert>
            </Stack>
          ) : (
            <GeneratedResult
              key={run.data.id}
              run={run.data}
              anotherPending={start.isPending}
              onAnother={() => startRun({ ...run.data.request, seed: null })}
            />
          )}
        </Box>
      </Box>
    </>
  );
}
