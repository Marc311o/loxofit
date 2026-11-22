import type { ReactNode } from "react";
import AddRounded from "@mui/icons-material/AddRounded";
import AutoAwesomeRounded from "@mui/icons-material/AutoAwesomeRounded";
import EventNoteRounded from "@mui/icons-material/EventNoteRounded";
import { Box, Button, Skeleton, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link as RouterLink, useNavigate } from "react-router";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { errorMessage } from "@/lib/api";
import { useActivePlan, useCreatePlan, usePlans } from "../api";
import { ActivePlanCard } from "../components/ActivePlanCard";
import { PlanListItem } from "../components/PlanListItem";

export function PlansPage() {
  const { t } = useTranslation(["plans", "common"]);
  const navigate = useNavigate();
  const plans = usePlans();
  const active = useActivePlan();
  const create = useCreatePlan();

  const handleCreate = () => {
    const count = (plans.data?.length ?? 0) + 1;
    create.mutate(
      { name: t("list.defaultName", { number: count }) },
      { onSuccess: (plan) => navigate(`/plans/${plan.id}`) },
    );
  };

  const actions = (
    <>
      <Button
        variant="outlined"
        startIcon={<AutoAwesomeRounded />}
        component={RouterLink}
        to="/plans/generate"
      >
        {t("actions.generate")}
      </Button>
      <Button
        variant="contained"
        startIcon={<AddRounded />}
        onClick={handleCreate}
        loading={create.isPending}
      >
        {t("actions.new")}
      </Button>
    </>
  );

  if (plans.isError || active.isError) {
    return (
      <>
        <PageHeader title={t("title")} actions={actions} />
        <EmptyState
          title={t("list.loadError")}
          description={errorMessage(plans.error ?? active.error)}
          action={
            <Button
              onClick={() => {
                void plans.refetch();
                void active.refetch();
              }}
            >
              {t("common:actions.tryAgain")}
            </Button>
          }
        />
      </>
    );
  }

  if (!plans.data || active.data === undefined) {
    return (
      <>
        <PageHeader title={t("title")} actions={actions} />
        <Stack spacing={2} aria-busy="true">
          <Skeleton variant="rounded" height={320} sx={{ borderRadius: 2 }} />
          <Skeleton variant="rounded" height={84} sx={{ borderRadius: 2 }} />
        </Stack>
      </>
    );
  }

  const drafts = plans.data.filter((p) => p.status === "draft");
  const archived = plans.data.filter((p) => p.status === "archived");

  return (
    <>
      <PageHeader title={t("title")} actions={actions} />
      {plans.data.length === 0 ? (
        <EmptyState
          icon={<EventNoteRounded />}
          title={t("list.emptyTitle")}
          description={t("list.emptyBody")}
          action={
            <Button variant="contained" onClick={handleCreate} loading={create.isPending}>
              {t("actions.new")}
            </Button>
          }
        />
      ) : (
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", lg: "minmax(0, 2fr) minmax(0, 1fr)" },
            gap: 3,
            alignItems: "start",
          }}
        >
          <Stack spacing={3} sx={{ minWidth: 0 }}>
            {active.data ? (
              <ActivePlanCard plan={active.data} />
            ) : (
              <EmptyState title={t("list.noActiveTitle")} description={t("list.noActiveBody")} />
            )}
            {archived.length > 0 && (
              <PlanSection title={t("list.archived")}>
                {archived.map((plan) => (
                  <PlanListItem key={plan.id} plan={plan} />
                ))}
              </PlanSection>
            )}
          </Stack>
          <PlanSection title={t("list.drafts")}>
            {drafts.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                {t("list.noDrafts")}
              </Typography>
            ) : (
              drafts.map((plan) => <PlanListItem key={plan.id} plan={plan} />)
            )}
          </PlanSection>
        </Box>
      )}
    </>
  );
}

function PlanSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Stack component="section" spacing={1.25} sx={{ minWidth: 0 }}>
      <Typography variant="overline" color="text.secondary" component="h2">
        {title}
      </Typography>
      {children}
    </Stack>
  );
}