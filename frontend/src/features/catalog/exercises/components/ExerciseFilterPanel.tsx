import { useState, type ReactNode } from "react";
import CloseRounded from "@mui/icons-material/CloseRounded";
import ExpandMoreRounded from "@mui/icons-material/ExpandMoreRounded";
import SearchRounded from "@mui/icons-material/SearchRounded";
import {
  Box,
  Button,
  Checkbox,
  Collapse,
  FormControlLabel,
  FormGroup,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import { TextInput } from "@/components/TextInput.tsx";
import {
  MOVEMENT_PATTERNS,
  type ExerciseType,
  type MovementPattern,
  type MuscleGroup,
} from "../../types.ts";
import type { ExerciseFilterState } from "../useExerciseFilters.ts";
import { BodyMap } from "../../components/BodyMap.tsx";
import { MuscleGroupList } from "./MuscleGroupList.tsx";

const EXERCISE_TYPES: ExerciseType[] = ["compound", "isolation"];

type ExerciseFilterPanelProps = {
  filters: ExerciseFilterState;
  onChange: (patch: Partial<ExerciseFilterState>) => void;
  onClear: () => void;
  hasActiveFilters: boolean;
  /** `false` when the user has not picked any equipment yet. */
  canFilterByEquipment: boolean;
  /** Exercises per muscle group for the other filters. */
  groupCounts: Record<MuscleGroup, number> | undefined;
  /** Rendered only when given - on phones the search box stays on the page. */
  search?: { value: string; onChange: (value: string) => void };
};

function FilterSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Stack spacing={1.25} component="section" aria-label={title}>
      <Typography variant="overline" color="text.secondary">
        {title}
      </Typography>
      {children}
    </Stack>
  );
}

export function ExerciseFilterPanel({
  filters,
  onChange,
  onClear,
  hasActiveFilters,
  canFilterByEquipment,
  groupCounts,
  search,
}: ExerciseFilterPanelProps) {
  const { t } = useTranslation("catalog");
  const [advancedOpen, setAdvancedOpen] = useState(filters.pattern !== null);

  const isTypeChecked = (type: ExerciseType) => filters.type === null || filters.type === type;
  const toggleType = (type: ExerciseType) => {
    const other = EXERCISE_TYPES.find((option) => option !== type)!;
    onChange({ type: filters.type === null ? other : null });
  };

  return (
    <Stack spacing={3}>
      {search && (
        <TextInput
          label={t("search")}
          type="search"
          value={search.value}
          onChange={search.onChange}
          icon={<SearchRounded />}
          autoComplete="off"
        />
      )}

      <FilterSection title={t("filters.muscleGroup")}>
        <BodyMap
          selected={filters.muscleGroup}
          onSelect={(muscleGroup) => onChange({ muscleGroup })}
        />
        <MuscleGroupList
          selected={filters.muscleGroup}
          onSelect={(muscleGroup) => onChange({ muscleGroup })}
          counts={groupCounts}
        />
      </FilterSection>

      <FilterSection title={t("filters.type")}>
        <FormGroup>
          {EXERCISE_TYPES.map((type) => {
            const checked = isTypeChecked(type);
            return (
              <FormControlLabel
                key={type}
                slotProps={{ typography: { variant: "body2" } }}
                label={t(`exercise.${type}`)}
                control={
                  <Checkbox
                    size="small"
                    checked={checked}
                    disabled={checked && filters.type === type}
                    onChange={() => toggleType(type)}
                  />
                }
              />
            );
          })}
        </FormGroup>
      </FilterSection>

      <FilterSection title={t("filters.equipment")}>
        <FormGroup>
          <FormControlLabel
            label={t("filters.myEquipmentOnly")}
            slotProps={{ typography: { variant: "body2" } }}
            control={
              <Checkbox
                size="small"
                checked={filters.mine && canFilterByEquipment}
                disabled={!canFilterByEquipment}
                onChange={(_, checked) => onChange({ mine: checked })}
              />
            }
          />
        </FormGroup>
        {!canFilterByEquipment && (
          <Typography variant="body2" color="text.secondary">
            {t("filters.myEquipmentHint")}
          </Typography>
        )}
      </FilterSection>

      <Box>
        <Button
          size="small"
          color="inherit"
          onClick={() => setAdvancedOpen((open) => !open)}
          aria-expanded={advancedOpen}
          endIcon={
            <ExpandMoreRounded
              sx={{
                transform: advancedOpen ? "rotate(180deg)" : "none",
                transition: "transform 150ms",
              }}
            />
          }
          sx={{ px: 0, color: "text.secondary" }}
        >
          {t("filters.advanced")}
        </Button>
        <Collapse in={advancedOpen}>
          <TextField
            select
            fullWidth
            size="small"
            label={t("filters.pattern")}
            value={filters.pattern ?? ""}
            onChange={(event) =>
              onChange({
                pattern: (event.target.value || null) as MovementPattern | null,
              })
            }
            slotProps={{
              select: { displayEmpty: true },
              inputLabel: { shrink: true },
            }}
            sx={{ mt: 1.5 }}
          >
            <MenuItem value="">{t("filters.anyPattern")}</MenuItem>
            {MOVEMENT_PATTERNS.map((pattern) => (
              <MenuItem key={pattern} value={pattern}>
                {t(`patterns.${pattern}`)}
              </MenuItem>
            ))}
          </TextField>
        </Collapse>
      </Box>

      {hasActiveFilters && (
        <Button variant="outlined" startIcon={<CloseRounded />} onClick={onClear}>
          {t("filters.clear")}
        </Button>
      )}
    </Stack>
  );
}
