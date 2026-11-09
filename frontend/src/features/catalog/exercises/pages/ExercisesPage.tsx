import { useState } from "react";
import CloseRounded from "@mui/icons-material/CloseRounded";
import SearchOffRounded from "@mui/icons-material/SearchOffRounded";
import SearchRounded from "@mui/icons-material/SearchRounded";
import TuneRounded from "@mui/icons-material/TuneRounded";
import {
  Badge,
  Box,
  Button,
  Drawer,
  IconButton,
  Pagination,
  Skeleton,
  Stack,
  Typography,
  useMediaQuery,
  type Theme,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { Outlet, useLocation } from "react-router";

import { EmptyState } from "@/components/EmptyState.tsx";
import { TextInput } from "@/components/TextInput.tsx";
import { useLanguage } from "@/i18n";
import { errorMessage } from "@/lib/api.ts";
import { useDebouncedCallback } from "@/lib/useDebouncedCallback.ts";
import { ExerciseFilterPanel } from "../components/ExerciseFilterPanel.tsx";
import { ExerciseRow } from "../components/ExerciseRow.tsx";
import type { ExerciseCountQuery, ExerciseQuery } from "../../types.ts";
import { useExerciseFilters } from "../useExerciseFilters.ts";
import { useMyEquipment } from "../../equipment/api";
import { useExerciseGroupCounts, useExercises } from "../api";

export function ExercisesPage() {
  const { t } = useTranslation(["catalog", "common"]);
  const language = useLanguage();
  const isDesktop = useMediaQuery((theme: Theme) => theme.breakpoints.up("md"));
  const [filtersOpen, setFiltersOpen] = useState(false);
  const { filters, setFilters, clearFilters, hasActiveFilters, activeFilterCount } =
    useExerciseFilters();
  const { search: locationSearch } = useLocation();

  const [searchInput, setSearchInput] = useState(filters.search);
  const [commitSearch, cancelSearch] = useDebouncedCallback(setFilters, 300);

  const myEquipment = useMyEquipment();
  const myEquipmentIds = myEquipment.data?.map((item) => item.id);
  const canFilterByEquipment = (myEquipmentIds?.length ?? 0) > 0;
  const waitingForEquipment = filters.mine && myEquipment.isPending;

  const countQuery: ExerciseCountQuery = {
    search: filters.search || undefined,
    pattern: filters.pattern ?? undefined,
    type: filters.type ?? undefined,
    availableWith: filters.mine && canFilterByEquipment ? myEquipmentIds : undefined,
  };
  const query: ExerciseQuery = {
    ...countQuery,
    page: filters.page,
    sort: language === "pl" ? "name_pl" : "name_en",
    muscleGroup: filters.muscleGroup ?? undefined,
  };
  const exercises = useExercises(query, { enabled: !waitingForEquipment });
  const groupCounts = useExerciseGroupCounts(countQuery, {
    enabled: !waitingForEquipment,
  });

  const handleSearchChange = (value: string) => {
    setSearchInput(value);
    commitSearch({ search: value });
  };

  const handleClear = () => {
    cancelSearch();
    setSearchInput("");
    clearFilters();
  };

  const handlePageChange = (page: number) => {
    setFilters({ page });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const search = { value: searchInput, onChange: handleSearchChange };
  const panelProps = {
    filters,
    onChange: setFilters,
    onClear: handleClear,
    hasActiveFilters,
    canFilterByEquipment,
    groupCounts: groupCounts.data,
  };

  let results;
  if (exercises.isError) {
    results = (
      <EmptyState
        title={t("list.loadError")}
        description={errorMessage(exercises.error)}
        action={<Button onClick={() => exercises.refetch()}>{t("common:actions.tryAgain")}</Button>}
      />
    );
  } else if (!exercises.data) {
    results = (
      <Stack spacing={1.25} aria-busy="true">
        {Array.from({ length: 6 }, (_, index) => (
          <Skeleton key={index} variant="rounded" height={82} sx={{ borderRadius: 5 }} />
        ))}
      </Stack>
    );
  } else if (exercises.data.items.length === 0) {
    results = (
      <EmptyState
        icon={<SearchOffRounded />}
        title={t("list.emptyTitle")}
        description={t("list.emptyBody")}
        action={hasActiveFilters && <Button onClick={handleClear}>{t("filters.clear")}</Button>}
      />
    );
  } else {
    const { items, total, pages } = exercises.data;
    results = (
      <>
        <Typography variant="overline" color="text.secondary" component="p">
          {t("list.count", { count: total })}
          {filters.muscleGroup && ` · ${t(`muscleGroups.${filters.muscleGroup}`)}`}
        </Typography>
        <Stack
          spacing={1.25}
          sx={{
            opacity: exercises.isPlaceholderData ? 0.6 : 1,
            transition: "opacity 150ms",
          }}
        >
          {items.map((exercise) => (
            <ExerciseRow
              key={exercise.id}
              exercise={exercise}
              to={{ pathname: String(exercise.id), search: locationSearch }}
            />
          ))}
        </Stack>
        {pages > 1 && (
          <Pagination
            count={pages}
            page={filters.page}
            onChange={(_, page) => handlePageChange(page)}
            color="primary"
            shape="rounded"
            sx={{ alignSelf: "center", pt: 1 }}
          />
        )}
      </>
    );
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
          aria-label={t("filters.title")}
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
          <Typography
            variant="overline"
            color="text.secondary"
            component="h2"
            sx={{ display: "block", mb: 2 }}
          >
            {t("filters.title")}
          </Typography>
          <ExerciseFilterPanel {...panelProps} search={search} />
        </Box>
      ) : (
        <>
          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <Box sx={{ flex: 1 }}>
              <TextInput
                label={t("search")}
                type="search"
                value={searchInput}
                onChange={handleSearchChange}
                icon={<SearchRounded />}
                autoComplete="off"
              />
            </Box>
            <IconButton
              aria-label={t("filters.title")}
              onClick={() => setFiltersOpen(true)}
              sx={{ border: 1, borderColor: "divider", width: 56, height: 56 }}
            >
              <Badge badgeContent={activeFilterCount} color="primary">
                <TuneRounded />
              </Badge>
            </IconButton>
          </Stack>
          <Drawer
            anchor="bottom"
            open={filtersOpen}
            onClose={() => setFiltersOpen(false)}
            slotProps={{
              paper: {
                sx: { borderRadius: "24px 24px 0 0", maxHeight: "88dvh" },
              },
            }}
          >
            <Stack
              direction="row"
              sx={{
                alignItems: "center",
                justifyContent: "space-between",
                px: 2.5,
                pt: 2,
              }}
            >
              <Typography variant="h3">{t("filters.title")}</Typography>
              <IconButton
                aria-label={t("common:actions.close")}
                onClick={() => setFiltersOpen(false)}
              >
                <CloseRounded />
              </IconButton>
            </Stack>
            <Box sx={{ px: 2.5, py: 2, overflowY: "auto" }}>
              <ExerciseFilterPanel {...panelProps} />
            </Box>
            <Box
              sx={{
                p: 2.5,
                pt: 1.5,
                pb: "calc(20px + env(safe-area-inset-bottom))",
                borderTop: 1,
                borderColor: "divider",
              }}
            >
              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={() => setFiltersOpen(false)}
              >
                {exercises.data
                  ? t("filters.showResults", { count: exercises.data.total })
                  : t("filters.showResultsPending")}
              </Button>
            </Box>
          </Drawer>
        </>
      )}

      <Stack spacing={1.5} sx={{ minWidth: 0 }}>
        {results}
      </Stack>
      <Outlet />
    </Box>
  );
}
