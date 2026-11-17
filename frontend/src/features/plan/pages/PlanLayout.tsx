import { useState } from "react";
import ArrowBackRounded from "@mui/icons-material/ArrowBackRounded";
import EditCalendarRounded from "@mui/icons-material/EditCalendarRounded";
import InsightsRounded from "@mui/icons-material/InsightsRounded";
import MoreVertRounded from "@mui/icons-material/MoreVertRounded";
import ViewWeekRounded from "@mui/icons-material/ViewWeekRounded";
import {
  Box,
  Button,
  Chip,
  IconButton,
  ListItemText,
  Menu,
  MenuItem,
  Skeleton,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link as RouterLink, Outlet, useMatch, useNavigate, useParams } from "react-router";

import { ConfirmDialog } from "@/components/ConfirmDialog";
import { EmptyState } from "@/components/EmptyState";
import { SegmentedControl } from "@/components/SegmentedControl";
import { errorMessage } from "@/lib/api";
import { toast } from "@/lib/toast";
import { FONT_MONO } from "@/styles/theme";
import { useActivatePlan, useDeletePlan, usePlan, useUpdatePlan } from "../api";
import { PlanSettingsDialog } from "../components/PlanSettingsDialog";
import type { PlanOutletContext } from "../planOutlet";
import type { PlanDetail } from "../types";

const TABS = [
  { value: "base", path: "", icon: <EditCalendarRounded fontSize="small" /> },
  { value: "weeks", path: "weeks", icon: <ViewWeekRounded fontSize="small" /> },
  { value: "analysis", path: "analysis", icon: <InsightsRounded fontSize="small" /> },
] as const;

export function PlanLayout() {
  const { planId = "" } = useParams();
  const { t } = useTranslation(["plans", "common"]);
  const plan = usePlan(planId);

  const weeksMatch = useMatch("/plans/:planId/weeks");
  const analysisMatch = useMatch("/plans/:planId/analysis");
  const tab = weeksMatch ? "weeks" : analysisMatch ? "analysis" : "base";

  const back = (
    <IconButton
      component={RouterLink}
      to="/plans"
      aria-label={t("actions.backToList")}
      sx={{ border: 1, borderColor: "divider", bgcolor: "background.paper", width: 44, height: 44 }}
    >
      <ArrowBackRounded />
    </IconButton>
  );

  if (plan.isError) {
    return (
      <Stack spacing={3}>
        <Box>{back}</Box>
        <EmptyState
          title={t("editor.loadError")}
          description={errorMessage(plan.error)}
          action={<Button onClick={() => plan.refetch()}>{t("common:actions.tryAgain")}</Button>}
        />
      </Stack>
    );
  }

  if (!plan.data) {
    return (
      <Stack spacing={3} aria-busy="true">
        <Skeleton variant="rounded" height={56} />
        <Skeleton variant="rounded" height={420} sx={{ borderRadius: 2 }} />
      </Stack>
    );
  }

  return (
    <Stack spacing={3}>
      <Stack direction="row" sx={{ alignItems: "center", gap: 2, flexWrap: "wrap" }}>
        {back}
        <Stack spacing={0.25} sx={{ mr: "auto", minWidth: 0 }}>
          <Typography variant="h1" sx={{ fontSize: { xs: 24, md: 28 } }} noWrap>
            {plan.data.name}
          </Typography>
          <Typography sx={{ fontFamily: FONT_MONO, fontSize: 11, color: "text.secondary" }}>
            {t(`status.${plan.data.status}`).toUpperCase()} ·{" "}
            {t("list.weeksCount", { count: plan.data.num_weeks }).toUpperCase()}
          </Typography>
        </Stack>
        <Stack
          direction="row"
          spacing={1}
          sx={{ alignItems: "center", flexWrap: "wrap", rowGap: 1 }}
        >
          <SegmentedControl
            label={t("tabs.label")}
            value={tab}
            iconsOnlyOnPhone
            options={TABS.map((item) => ({
              value: item.value,
              label: t(`tabs.${item.value}`),
              icon: item.icon,
              to: item.path === "" ? `/plans/${planId}` : `/plans/${planId}/${item.path}`,
            }))}
          />
          <PlanActions plan={plan.data} />
        </Stack>
      </Stack>

      <Outlet context={{ plan: plan.data } satisfies PlanOutletContext} />
    </Stack>
  );
}

function PlanActions({ plan }: { plan: PlanDetail }) {
  const { t } = useTranslation("plans");
  const navigate = useNavigate();
  const [menuAnchor, setMenuAnchor] = useState<HTMLElement | null>(null);
  const [dialog, setDialog] = useState<"settings" | "delete" | null>(null);

  const update = useUpdatePlan(plan.id);
  const activate = useActivatePlan(plan.id);
  const remove = useDeletePlan(plan.id);

  const complete = plan.weeks.length === plan.num_weeks;
  const archived = plan.status === "archived";

  const closeMenu = () => setMenuAnchor(null);
  const open = (which: "settings" | "delete") => {
    closeMenu();
    setDialog(which);
  };

  return (
    <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
      {plan.status === "active" ? (
        <Chip color="primary" label={t("status.active")} />
      ) : (
        <Tooltip title={complete ? "" : t("editor.activateIncomplete")}>
          <span>
            <Button
              variant="contained"
              disabled={!complete}
              loading={activate.isPending}
              onClick={() =>
                activate.mutate(undefined, {
                  onSuccess: () => toast.success(t("editor.activated")),
                })
              }
            >
              {t("actions.activate")}
            </Button>
          </span>
        </Tooltip>
      )}

      <IconButton
        aria-label={t("actions.more")}
        aria-haspopup="menu"
        onClick={(e) => setMenuAnchor(e.currentTarget)}
        sx={{ border: 1, borderColor: "divider", width: 44, height: 44 }}
      >
        <MoreVertRounded />
      </IconButton>
      <Menu anchorEl={menuAnchor} open={menuAnchor !== null} onClose={closeMenu}>
        <MenuItem onClick={() => open("settings")} disabled={archived}>
          <ListItemText>{t("actions.settings")}</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => open("delete")} sx={{ color: "error.main" }}>
          <ListItemText>{t("actions.delete")}</ListItemText>
        </MenuItem>
      </Menu>

      {dialog === "settings" && (
        <PlanSettingsDialog
          plan={plan}
          open
          saving={update.isPending}
          onClose={() => setDialog(null)}
          onSave={(data) =>
            update.mutate(data, {
              onSuccess: () => {
                setDialog(null);
                toast.success(t("settings.saved"));
              },
            })
          }
        />
      )}
      <ConfirmDialog
        open={dialog === "delete"}
        title={t("editor.deleteTitle", { name: plan.name })}
        description={t("editor.deleteBody")}
        confirmLabel={t("actions.delete")}
        cancelLabel={t("actions.cancel")}
        destructive
        loading={remove.isPending}
        onCancel={() => setDialog(null)}
        onConfirm={() =>
          remove.mutate(undefined, {
            onSuccess: () => {
              toast.success(t("editor.deleted"));
              navigate("/plans");
            },
          })
        }
      />
    </Stack>
  );
}