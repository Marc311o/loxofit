import { useState } from "react";
import CloseRounded from "@mui/icons-material/CloseRounded";
import InfoOutlined from "@mui/icons-material/InfoOutlined";
import SearchRounded from "@mui/icons-material/SearchRounded";
import {
  Box,
  Checkbox,
  Chip,
  Dialog,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Pagination,
  Skeleton,
  Stack,
  Typography,
  useMediaQuery,
  type Theme,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import { TextInput } from "@/components/TextInput";
import { useMyEquipment } from "@/features/catalog/equipment/api";
import { useExercises } from "@/features/catalog/exercises/api";
import { ExerciseThumbnail } from "@/features/catalog/exercises/components/ExerciseThumbnail";
import { MUSCLE_GROUPS, type MuscleGroup } from "@/features/catalog/types";
import { useLanguage } from "@/i18n";
import { useLocalizedName } from "@/i18n/useLocalized";
import { useDebouncedCallback } from "@/lib/useDebouncedCallback";
import { ExerciseInfoDialog } from "./ExerciseInfoDialog";

type ExercisePickerDialogProps = {
  sessionName: string;
  excludedIds: ReadonlySet<number>;
  suggestedGroups: MuscleGroup[];
  onPick: (exerciseId: number) => void;
  onClose: () => void;
};

/**
 * Quick exercise search for the plan editor, built from the catalog's pieces.
 * Filters live in local state, not in the URL - the editor's URL stays as is.
 * Mounted only while open, so every opening starts with fresh filters.
 */
export function ExercisePickerDialog({
  sessionName,
  excludedIds,
  suggestedGroups,
  onPick,
  onClose,
}: ExercisePickerDialogProps) {
  const { t } = useTranslation(["plans", "catalog"]);
  const language = useLanguage();
  const localizedName = useLocalizedName();
  const fullScreen = useMediaQuery((theme: Theme) => theme.breakpoints.down("sm"));

  const myEquipment = useMyEquipment();
  const equipmentIds = myEquipment.data?.map((e) => e.id) ?? [];
  const hasEquipment = equipmentIds.length > 0;

  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [group, setGroup] = useState<MuscleGroup | null>(null);
  const [onlyMine, setOnlyMine] = useState(true);
  const [page, setPage] = useState(1);
  const [infoId, setInfoId] = useState<number | null>(null);
  const [commitSearch] = useDebouncedCallback((value: string) => {
    setSearch(value.trim());
    setPage(1);
  }, 300);

  const filterMine = onlyMine && hasEquipment;
  const exercises = useExercises(
    {
      search: search || undefined,
      muscleGroup: group ?? undefined,
      availableWith: filterMine ? equipmentIds : undefined,
      sort: language === "pl" ? "name_pl" : "name_en",
      page,
    },
    { enabled: !(onlyMine && myEquipment.isPending) },
  );

  const chooseGroup = (next: MuscleGroup | null) => {
    setGroup(next);
    setPage(1);
  };

  const groups = [...suggestedGroups, ...MUSCLE_GROUPS.filter((g) => !suggestedGroups.includes(g))];

  return (
    <Dialog
      open
      onClose={onClose}
      fullScreen={fullScreen}
      fullWidth
      maxWidth="sm"
      aria-labelledby="exercise-picker-title"
      slotProps={{ paper: { sx: { height: fullScreen ? undefined : "min(780px, 90dvh)" } } }}
    >
      <DialogTitle id="exercise-picker-title" sx={{ pr: 7 }}>
        {t("picker.title", { session: sessionName })}
        <IconButton
          aria-label={t("actions.close")}
          onClick={onClose}
          sx={{ position: "absolute", right: 12, top: 12 }}
        >
          <CloseRounded />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        <TextInput
          label={t("catalog:search")}
          type="search"
          value={searchInput}
          onChange={(value) => {
            setSearchInput(value);
            commitSearch(value);
          }}
          icon={<SearchRounded />}
          autoComplete="off"
          autoFocus
        />

        {suggestedGroups.length > 0 && (
          <Typography variant="body2" color="text.secondary">
            {t("picker.suggested")}
          </Typography>
        )}
        <Box
          role="group"
          aria-label={t("catalog:filters.muscleGroup")}
          sx={{ display: "flex", flexWrap: "wrap", gap: 0.75 }}
        >
          <Chip
            label={t("picker.allGroups")}
            color={group === null ? "primary" : "default"}
            variant={group === null ? "filled" : "outlined"}
            onClick={() => chooseGroup(null)}
            aria-pressed={group === null}
          />
          {groups.map((g) => {
            const selected = group === g;
            const suggested = suggestedGroups.includes(g);
            return (
              <Chip
                key={g}
                label={t(`catalog:muscleGroups.${g}`)}
                color={selected ? "primary" : suggested ? "warning" : "default"}
                variant={selected ? "filled" : "outlined"}
                onClick={() => chooseGroup(selected ? null : g)}
                aria-pressed={selected}
              />
            );
          })}
        </Box>

        <FormControlLabel
          control={
            <Checkbox
              checked={filterMine}
              disabled={!hasEquipment}
              onChange={(e) => {
                setOnlyMine(e.target.checked);
                setPage(1);
              }}
            />
          }
          label={hasEquipment ? t("picker.onlyMine") : t("picker.noEquipment")}
        />

        {exercises.data ? (
          exercises.data.items.length === 0 ? (
            <Typography color="text.secondary" sx={{ py: 4, textAlign: "center" }}>
              {t("picker.empty")}
            </Typography>
          ) : (
            <List
              disablePadding
              sx={{ opacity: exercises.isPlaceholderData ? 0.6 : 1, transition: "opacity 150ms" }}
            >
              {exercises.data.items.map((exercise) => {
                const taken = excludedIds.has(exercise.id);
                const name = localizedName(exercise);
                return (
                  <ListItem
                    key={exercise.id}
                    disablePadding
                    secondaryAction={
                      <IconButton
                        edge="end"
                        aria-label={t("picker.details", { exercise: name })}
                        onClick={() => setInfoId(exercise.id)}
                      >
                        <InfoOutlined />
                      </IconButton>
                    }
                  >
                    <ListItemButton
                      disabled={taken}
                      onClick={() => onPick(exercise.id)}
                      sx={{ borderRadius: 1, gap: 1.5, px: 1 }}
                    >
                      <ExerciseThumbnail imageUrl={exercise.image_url} size={40} />
                      <ListItemText
                        primary={name}
                        secondary={
                          taken
                            ? t("picker.inSession")
                            : `${t(`catalog:muscleGroups.${exercise.main_group}`)} · ${t(
                                exercise.is_compound
                                  ? "catalog:exercise.compound"
                                  : "catalog:exercise.isolation",
                              )}`
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                );
              })}
            </List>
          )
        ) : (
          <Stack spacing={1} aria-busy="true">
            {Array.from({ length: 6 }, (_, i) => (
              <Skeleton key={i} variant="rounded" height={52} />
            ))}
          </Stack>
        )}

        {exercises.data && exercises.data.pages > 1 && (
          <Pagination
            count={exercises.data.pages}
            page={page}
            onChange={(_, value) => setPage(value)}
            shape="rounded"
            color="primary"
            sx={{ alignSelf: "center" }}
          />
        )}
      </DialogContent>
      {infoId !== null && (
        <ExerciseInfoDialog exerciseId={infoId} onClose={() => setInfoId(null)} />
      )}
    </Dialog>
  );
}
