import { Box, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { useMuscles } from "@/features/catalog/muscles/api";
import { useFormatNumber, useLocalizedName } from "@/i18n/useLocalized";
import { zoneColors } from "@/styles/theme";
import type { PlanIssue } from "../insights";

type IssueListProps = {
  issues: PlanIssue[];
  sessionNames: string[];
  inverted?: boolean;
  limit?: number;
};

const DOT: Record<PlanIssue["kind"], string> = {
  aboveMrv: zoneColors.aboveMrv,
  overtime: zoneColors.aboveMrv,
  belowMev: zoneColors.belowMev,
  capped: zoneColors.belowMev,
};

export function IssueList({ issues, sessionNames, inverted = false, limit }: IssueListProps) {
  const { t } = useTranslation("plans");
  const muscles = useMuscles();
  const localizedName = useLocalizedName();
  const formatNumber = useFormatNumber();

  const muscleName = (id: number) => {
    const muscle = muscles.data?.find((m) => m.id === id);
    return muscle ? localizedName(muscle) : "…";
  };

  const text = (issue: PlanIssue) => {
    switch (issue.kind) {
      case "aboveMrv":
        return t("issues.aboveMrv", {
          muscle: muscleName(issue.muscleId),
          week: issue.week,
          sets: formatNumber(issue.volume, 1),
        });
      case "belowMev":
        return t("issues.belowMev", {
          muscle: muscleName(issue.muscleId),
          sets: formatNumber(issue.volume, 1),
        });
      case "capped":
        return t("issues.capped", {
          muscle: muscleName(issue.muscleId),
          sets: formatNumber(issue.lost, 1),
          week: issue.week,
        });
      case "overtime":
        return t("issues.overtime", {
          session: sessionNames[issue.session] ?? "",
          minutes: Math.ceil(issue.minutes),
          week: issue.week,
        });
    }
  };

  if (issues.length === 0) {
    return (
      <Typography variant="body2" sx={{ color: inverted ? "#E4F1EC" : "text.secondary" }}>
        {t("issues.none")}
      </Typography>
    );
  }

  const shown = limit === undefined ? issues : issues.slice(0, limit);
  const hidden = issues.length - shown.length;

  return (
    <Stack component="ul" spacing={1} sx={{ m: 0, p: 0, listStyle: "none" }}>
      {shown.map((issue) => (
        <Stack
          component="li"
          key={`${issue.kind}-${"muscleId" in issue ? issue.muscleId : issue.session}`}
          direction="row"
          spacing={1.25}
          sx={{ alignItems: "flex-start" }}
        >
          <Box
            aria-hidden
            sx={{
              width: 8,
              height: 8,
              mt: 0.75,
              flexShrink: 0,
              borderRadius: 1,
              bgcolor: DOT[issue.kind],
            }}
          />
          <Typography variant="body2" sx={{ color: inverted ? "#E4F1EC" : "text.primary" }}>
            {text(issue)}
          </Typography>
        </Stack>
      ))}
      {hidden > 0 && (
        <Typography
          component="li"
          variant="body2"
          sx={{ color: inverted ? "#A9CFC4" : "text.secondary" }}
        >
          {t("issues.more", { count: hidden })}
        </Typography>
      )}
    </Stack>
  );
}
