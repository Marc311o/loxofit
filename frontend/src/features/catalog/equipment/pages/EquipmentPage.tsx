import { useEffect, useMemo, useState } from "react";
import { Box, Button, Skeleton, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useBlocker } from "react-router";
import { InfoHint } from "@/components/InfoHint";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { EmptyState } from "@/components/EmptyState";
import { errorMessage } from "@/lib/api";
import { toast } from "@/lib/toast";
import { useExerciseGroupCounts } from "../../exercises/api";
import type { Equipment, EquipmentCategory } from "../../types";
import { useEquipmentCatalog, useMyEquipment, useSaveMyEquipment } from "../api";
import { EquipmentSaveBar } from "../components/EquipmentSaveBar";
import { EquipmentSection } from "../components/EquipmentSection";

const CATEGORIES: EquipmentCategory[] = ["free_weights", "station", "cable", "machine"];

function sameIds(a: ReadonlySet<number>, b: ReadonlySet<number>): boolean {
  return a.size === b.size && [...a].every((id) => b.has(id));
}

/** The user's equipment: tick what you have access to, then save. */
export function EquipmentPage() {
  const { t } = useTranslation(["catalog", "common"]);
  const catalog = useEquipmentCatalog();
  const mine = useMyEquipment();
  const save = useSaveMyEquipment();

  const [draft, setDraft] = useState<ReadonlySet<number> | null>(null);
  const saved = useMemo(() => new Set(mine.data?.map((item) => item.id)), [mine.data]);
  const selected = draft ?? saved;
  const dirty = draft !== null && !sameIds(draft, saved);

  const selectedIds = [...selected].sort((a, b) => a - b);
  const counts = useExerciseGroupCounts(
    { availableWith: selectedIds },
    { enabled: selectedIds.length > 0 },
  );
  const availableExercises = counts.data
    ? Object.values(counts.data).reduce((sum, count) => sum + count, 0)
    : null;

  const byCategory = useMemo(() => {
    const groups = new Map<EquipmentCategory, Equipment[]>(
      CATEGORIES.map((category) => [category, []]),
    );
    catalog.data?.forEach((item) => groups.get(item.category)?.push(item));
    return groups;
  }, [catalog.data]);

  const update = (change: (next: Set<number>) => void) => {
    const next = new Set(selected);
    change(next);
    setDraft(next);
  };
  const toggle = (id: number) => update((next) => (next.has(id) ? next.delete(id) : next.add(id)));
  const toggleMany = (ids: number[], checked: boolean) =>
    update((next) => ids.forEach((id) => (checked ? next.add(id) : next.delete(id))));

  const handleSave = () =>
    save.mutate([...selected], {
      onSuccess: () => {
        setDraft(null);
        toast.success(t("equipment.saved"));
      },
    });

  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      dirty && currentLocation.pathname !== nextLocation.pathname,
  );
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  if (catalog.isError || mine.isError) {
    return (
      <EmptyState
        title={t("equipment.loadError")}
        description={errorMessage(catalog.error ?? mine.error)}
        action={
          <Button
            onClick={() => {
              void catalog.refetch();
              void mine.refetch();
            }}
          >
            {t("common:actions.tryAgain")}
          </Button>
        }
      />
    );
  }

  if (!catalog.data || !mine.data) {
    return (
      <Box
        aria-busy="true"
        sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "repeat(2, minmax(0, 1fr))",
            sm: "repeat(auto-fill, minmax(160px, 1fr))",
          },
          gap: 1.5,
        }}
      >
        {Array.from({ length: 8 }, (_, index) => (
          <Skeleton
            key={index}
            variant="rounded"
            sx={{ aspectRatio: "0.8", height: "auto", borderRadius: "20px" }}
          />
        ))}
      </Box>
    );
  }

  const summary = [
    t("equipment.selected", {
      selected: selected.size,
      total: catalog.data.length,
    }),
    selected.size === 0
      ? t("equipment.bodyweightOnly")
      : availableExercises !== null && t("equipment.available", { count: availableExercises }),
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <Stack spacing={2.5}>
      <Stack
        direction="row"
        spacing={1}
        useFlexGap
        sx={{
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {summary}
        </Typography>
        <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
          <InfoHint text={t("equipment.intro")} />
          <Button
            size="small"
            onClick={() =>
              toggleMany(
                catalog.data.map((item) => item.id),
                true,
              )
            }
          >
            {t("equipment.selectAll")}
          </Button>
          <Button size="small" color="inherit" onClick={() => setDraft(new Set())}>
            {t("equipment.clearAll")}
          </Button>
        </Stack>
      </Stack>

      <Stack spacing={3}>
        {CATEGORIES.filter((category) => byCategory.get(category)!.length > 0).map((category) => (
          <EquipmentSection
            key={category}
            category={category}
            items={byCategory.get(category)!}
            saved={saved}
            selected={selected}
            onToggle={toggle}
          />
        ))}
      </Stack>

      <EquipmentSaveBar
        open={dirty}
        summary={summary}
        saving={save.isPending}
        onDiscard={() => setDraft(null)}
        onSave={handleSave}
      />

      <ConfirmDialog
        open={blocker.state === "blocked"}
        title={t("equipment.leaveTitle")}
        description={t("equipment.leaveBody")}
        confirmLabel={t("equipment.leave")}
        cancelLabel={t("equipment.stay")}
        destructive
        onConfirm={() => blocker.proceed?.()}
        onCancel={() => blocker.reset?.()}
      />
    </Stack>
  );
}
