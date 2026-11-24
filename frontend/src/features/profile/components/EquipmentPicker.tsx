import { useMemo, useState } from "react";
import CottageOutlined from "@mui/icons-material/CottageOutlined";
import FitnessCenterRounded from "@mui/icons-material/FitnessCenterRounded";
import TuneRounded from "@mui/icons-material/TuneRounded";
import WarehouseOutlined from "@mui/icons-material/WarehouseOutlined";
import { Box, ButtonBase, Skeleton, Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import {
  type EquipmentPresetCode,
  useEquipmentCatalog,
  useEquipmentPresets,
} from "@/features/catalog/equipment/api";
import { EquipmentSection } from "@/features/catalog/equipment/components/EquipmentSection";
import { useExerciseGroupCounts } from "@/features/catalog/exercises/api";
import type { Equipment, EquipmentCategory } from "@/features/catalog/types";

const CATEGORIES: EquipmentCategory[] = ["free_weights", "station", "cable", "machine"];
const PRESET_ICONS: Record<EquipmentPresetCode, ReactNode> = {
  gym: <FitnessCenterRounded />,
  home_barbell: <WarehouseOutlined />,
  home_dumbbells: <CottageOutlined />,
};

type EquipmentPickerProps = {
  selected: ReadonlySet<number>;
  onChange: (selected: ReadonlySet<number>) => void;
};

const sameIds = (a: ReadonlySet<number>, b: readonly number[]) =>
  a.size === b.length && b.every((id) => a.has(id));

/** A ready-made set in one click, or tile by tile - the same tiles as in the catalog. */
export function EquipmentPicker({ selected, onChange }: EquipmentPickerProps) {
  const { t } = useTranslation("profile");
  const presets = useEquipmentPresets();
  const catalog = useEquipmentCatalog();
  const [custom, setCustom] = useState(false);

  const matching = presets.data?.find((p) => sameIds(selected, p.equipment_ids))?.code ?? null;
  const showList = custom || (selected.size > 0 && matching === null);

  const selectedIds = [...selected].sort((a, b) => a - b);
  const counts = useExerciseGroupCounts(
    { availableWith: selectedIds },
    { enabled: selectedIds.length > 0 },
  );
  const exercises = counts.data ? Object.values(counts.data).reduce((a, b) => a + b, 0) : null;

  const byCategory = useMemo(() => {
    const groups = new Map<EquipmentCategory, Equipment[]>(CATEGORIES.map((c) => [c, []]));
    catalog.data?.forEach((item) => groups.get(item.category)?.push(item));
    return groups;
  }, [catalog.data]);

  const toggle = (id: number) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onChange(next);
  };

  if (!presets.data || !catalog.data) {
    return (
      <Box sx={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 1.5 }}>
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} variant="rounded" height={96} />
        ))}
      </Box>
    );
  }

  return (
    <Stack spacing={2.5}>
      <Box
        role="radiogroup"
        aria-label={t("equipment.label")}
        sx={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 1.5 }}
      >
        {presets.data.map((preset) => (
          <OptionCard
            key={preset.code}
            icon={PRESET_ICONS[preset.code]}
            title={t(`equipment.presets.${preset.code}.label`)}
            description={t(`equipment.presets.${preset.code}.description`)}
            selected={!showList && matching === preset.code}
            onClick={() => {
              setCustom(false);
              onChange(new Set(preset.equipment_ids));
            }}
          />
        ))}
        <OptionCard
          icon={<TuneRounded />}
          title={t("equipment.custom.label")}
          description={t("equipment.custom.description")}
          selected={showList}
          onClick={() => setCustom(true)}
        />
      </Box>

      <Typography variant="body2" sx={{ fontWeight: 600 }} aria-live="polite">
        {selected.size === 0
          ? t("equipment.none")
          : [
              t("equipment.selected", { count: selected.size }),
              exercises !== null && t("equipment.exercises", { count: exercises }),
            ]
              .filter(Boolean)
              .join(" · ")}
      </Typography>

      {showList && (
        <Stack spacing={3}>
          {CATEGORIES.filter((c) => byCategory.get(c)!.length > 0).map((category) => (
            <EquipmentSection
              key={category}
              category={category}
              items={byCategory.get(category)!}
              saved={selected}
              selected={selected}
              onToggle={toggle}
            />
          ))}
        </Stack>
      )}
    </Stack>
  );
}

function OptionCard({
  icon,
  title,
  description,
  selected,
  onClick,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <ButtonBase
      role="radio"
      aria-checked={selected}
      onClick={onClick}
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
        gap: 0.5,
        p: 1.5,
        textAlign: "left",
        border: 1,
        borderRadius: 2,
        borderColor: selected ? "primary.main" : "divider",
        bgcolor: selected ? "primary.light" : "transparent",
        color: "text.primary",
        transition: "border-color 120ms, background-color 120ms",
        "&:hover": { borderColor: "primary.main" },
        "&.Mui-focusVisible": { outline: 2, outlineColor: "primary.main", outlineOffset: 2 },
        "& svg": { color: selected ? "primary.main" : "text.secondary" },
      }}
    >
      {icon}
      <Typography sx={{ fontSize: 14, fontWeight: 600, lineHeight: 1.3 }}>{title}</Typography>
      <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.35 }}>
        {description}
      </Typography>
    </ButtonBase>
  );
}
