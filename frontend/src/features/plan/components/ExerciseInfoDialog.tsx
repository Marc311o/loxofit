import CloseRounded from "@mui/icons-material/CloseRounded";
import {
  Dialog,
  DialogContent,
  IconButton,
  Skeleton,
  Stack,
  Typography,
  useMediaQuery,
  type Theme,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import { useExercise } from "@/features/catalog/exercises/api";
import { ExerciseDetailContent } from "@/features/catalog/exercises/components/ExerciseDetailContent";
import { errorMessage } from "@/lib/api";

type ExerciseInfoDialogProps = {
  exerciseId: number;
  onClose: () => void;
};

/**
 * The catalog's exercise details on top of the editor or the picker, so the user
 * can check which muscles an exercise trains without leaving the plan.
 */
export function ExerciseInfoDialog({ exerciseId, onClose }: ExerciseInfoDialogProps) {
  const { t } = useTranslation("plans");
  const fullScreen = useMediaQuery((theme: Theme) => theme.breakpoints.down("sm"));
  const exercise = useExercise(exerciseId);

  return (
    <Dialog
      open
      onClose={onClose}
      fullScreen={fullScreen}
      fullWidth
      maxWidth="sm"
      aria-labelledby="exercise-title"
    >
      <IconButton
        aria-label={t("actions.close")}
        onClick={onClose}
        sx={{ position: "absolute", top: 12, right: 12, zIndex: 1 }}
      >
        <CloseRounded />
      </IconButton>
      <DialogContent sx={{ px: { xs: 2.5, sm: 4 }, pt: { xs: 7, sm: 4 }, pb: 4 }}>
        {exercise.data ? (
          <ExerciseDetailContent exercise={exercise.data} />
        ) : exercise.isError ? (
          <Typography color="error">{errorMessage(exercise.error)}</Typography>
        ) : (
          <Stack spacing={2} aria-busy="true">
            <Skeleton width="30%" />
            <Skeleton variant="rounded" height={36} width="75%" />
            <Skeleton variant="rounded" height={160} />
          </Stack>
        )}
      </DialogContent>
    </Dialog>
  );
}