import { useMemo } from "react";
import { Box, Button, Skeleton, Stack, Typography, useMediaQuery, type Theme } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router";

import { EmptyState } from "@/components/EmptyState";
import { errorMessage } from "@/lib/api";
import { BodyMap } from "../../components/BodyMap";
import { MuscleGroupList } from "../components/MuscleGroupList";
import { MUSCLE_GROUPS, type Muscle, type MuscleGroup } from "../../types";
import { useMuscles } from "../api";
import { MuscleCard } from "../components/MuscleCard";

function parseGroup(value: string | null): MuscleGroup | null {
  return MUSCLE_GROUPS.find((group) => group === value) ?? null;
}

export function MusclesPage() {
  const { t } = useTranslation(["catalog", "common"]);
  const isDesktop = useMediaQuery((theme: Theme) => theme.breakpoints.up("md"));
  const [params, setParams] = useSearchParams();
  const selected = parseGroup(params.get("group"));
  const muscles = useMuscles();

  // The group is kept in the URL like on the exercises page.
  const select = (group: MuscleGroup | null) =>
    setParams(group ? { group } : {}, { replace: true });

  const byGroup = useMemo(() => {
    const groups = new Map<MuscleGroup, Muscle[]>(MUSCLE_GROUPS.map((group) => [group, []]));
    muscles.data?.forEach((muscle) => groups.get(muscle.muscle_group)!.push(muscle));
    return groups;
  }, [muscles.data]);

  const counts = muscles.data
    ? (Object.fromEntries(
        MUSCLE_GROUPS.map((group) => [group, byGroup.get(group)!.length]),
      ) as Record<MuscleGroup, number>)
    : undefined;

  const visibleGroups = MUSCLE_GROUPS.filter(
    (group) => (selected === null || group === selected) && byGroup.get(group)!.length > 0,
  );

  let content;
  if (muscles.isError) {
    content = (
      <EmptyState
        title={t("muscles.loadError")}
        description={errorMessage(muscles.error)}
        action={<Button onClick={() => muscles.refetch()}>{t("common:actions.tryAgain")}</Button>}
      />
    );
  } else if (!muscles.data) {
    content = (
      <Stack spacing={1.25} aria-busy="true">
        {Array.from({ length: 5 }, (_, index) => (
          <Skeleton key={index} variant="rounded" height={76} />
        ))}
      </Stack>
    );
  } else {
    content = visibleGroups.map((group) => (
      <Stack key={group} spacing={1.25} component="section" aria-labelledby={`group-${group}`}>
        <Typography id={`group-${group}`} variant="overline" color="text.secondary" component="h2">
          {t(`muscleGroups.${group}`)}
        </Typography>
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" },
            gap: 1.25,
          }}
        >
          {byGroup.get(group)!.map((muscle) => (
            <MuscleCard key={muscle.id} muscle={muscle} />
          ))}
        </Box>
      </Stack>
    ));
  }

  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: { xs: "1fr", md: "300px 1fr" },
        gap: 3,
        alignItems: "start",
      }}
    >
      {isDesktop ? (
        <Box
          component="aside"
          aria-label={t("filters.muscleGroup")}
          sx={{
            position: "sticky",
            top: 24,
            maxHeight: "calc(100dvh - 48px)",
            overflowY: "auto",
            pr: 1,
            scrollbarWidth: "none",
            "&::-webkit-scrollbar": { display: "none" },
          }}
        >
          <Stack spacing={1.25}>
            <Typography variant="overline" color="text.secondary" component="h2">
              {t("filters.muscleGroup")}
            </Typography>
            <BodyMap selected={selected} onSelect={select} />
            <MuscleGroupList selected={selected} onSelect={select} counts={counts} />
          </Stack>
        </Box>
      ) : (
        <Stack spacing={1.5} sx={{ alignItems: "center" }}>
          <Box sx={{ width: "100%", maxWidth: 280 }}>
            <BodyMap selected={selected} onSelect={select} />
          </Box>
        </Stack>
      )}

      <Stack spacing={3} sx={{ minWidth: 0 }}>
        {content}
      </Stack>
    </Box>
  );
}
