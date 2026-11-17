import ChevronRightRounded from "@mui/icons-material/ChevronRightRounded";
import { Card, CardActionArea, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router";

import { FONT_DISPLAY, FONT_MONO } from "@/styles/theme";
import { useFormatDate } from "../format";
import type { PlanSummary } from "../types";

/** A draft or an archived plan in the list. */
export function PlanListItem({ plan }: { plan: PlanSummary }) {
  const { t } = useTranslation("plans");
  const formatDate = useFormatDate();

  return (
    <Card>
      <CardActionArea
        component={RouterLink}
        to={`/plans/${plan.id}`}
        sx={{ display: "flex", alignItems: "center", gap: 1.5, p: 2 }}
      >
        <Stack spacing={0.5} sx={{ flex: 1, minWidth: 0 }}>
          <Typography sx={{ fontFamily: FONT_DISPLAY, fontSize: 18, fontWeight: 600 }} noWrap>
            {plan.name}
          </Typography>
          <Typography sx={{ fontFamily: FONT_MONO, fontSize: 11, color: "text.secondary" }}>
            {t("list.meta", { count: plan.num_weeks, date: formatDate(plan.updated_at) })}
          </Typography>
        </Stack>
        <ChevronRightRounded sx={{ color: "text.secondary" }} aria-hidden />
      </CardActionArea>
    </Card>
  );
}