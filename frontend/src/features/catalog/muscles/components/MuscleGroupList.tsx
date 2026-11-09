import { ButtonBase, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { FONT_MONO } from "@/styles/theme";
import { MUSCLE_GROUPS, type MuscleGroup } from "../../types";

type MuscleGroupListProps = {
  selected: MuscleGroup | null;
  onSelect: (group: MuscleGroup | null) => void;
  counts: Record<MuscleGroup, number> | undefined;
};

type RowProps = {
  label: string;
  count: number | undefined;
  selected: boolean;
  onClick: () => void;
};

function GroupRow({ label, count, selected, onClick }: RowProps) {
  return (
    <ButtonBase
      onClick={onClick}
      aria-pressed={selected}
      disabled={count === 0 && !selected}
      sx={{
        width: "100%",
        justifyContent: "space-between",
        gap: 1,
        px: 1.5,
        py: 1,
        borderRadius: 1,
        fontSize: 14,
        fontWeight: selected ? 600 : 500,
        bgcolor: selected ? "primary.main" : "transparent",
        color: selected ? "primary.contrastText" : "text.primary",
        "&:hover": { bgcolor: selected ? "primary.dark" : "action.hover" },
        "&.Mui-disabled": { color: "text.disabled" },
        "&.Mui-focusVisible": { outline: 2, outlineColor: "primary.main" },
      }}
    >
      <span>{label}</span>
      <Typography
        component="span"
        sx={{
          fontFamily: FONT_MONO,
          fontSize: 12,
          color: selected ? "primary.light" : "text.secondary",
        }}
      >
        {count ?? "·"}
      </Typography>
    </ButtonBase>
  );
}

/** Muscle groups with exercise counts; clicking the selected group clears it. */
export function MuscleGroupList({ selected, onSelect, counts }: MuscleGroupListProps) {
  const { t } = useTranslation("catalog");
  const total = counts ? Object.values(counts).reduce((sum, count) => sum + count, 0) : undefined;

  return (
    <Stack spacing={0.25} role="group" aria-label={t("filters.muscleGroup")}>
      <GroupRow
        label={t("filters.all")}
        count={total}
        selected={selected === null}
        onClick={() => onSelect(null)}
      />
      {MUSCLE_GROUPS.map((group) => (
        <GroupRow
          key={group}
          label={t(`muscleGroups.${group}`)}
          count={counts?.[group]}
          selected={selected === group}
          onClick={() => onSelect(selected === group ? null : group)}
        />
      ))}
    </Stack>
  );
}
