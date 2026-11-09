import CloseRounded from "@mui/icons-material/CloseRounded";
import {
  Button,
  Dialog,
  DialogContent,
  IconButton,
  Skeleton,
  Stack,
  useMediaQuery,
  type Theme,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate, useParams } from "react-router";

import { EmptyState } from "@/components/EmptyState.tsx";
import { ApiError, errorMessage } from "@/lib/api.ts";
import { useExercise } from "../api.ts";
import { ExerciseDetailContent } from "../components/ExerciseDetailContent.tsx";

function parseId(value: string | undefined): number | null {
  const id = Number(value);
  return Number.isInteger(id) && id > 0 ? id : null;
}

function DetailSkeleton() {
  return (
    <Stack spacing={2} aria-busy="true">
      <Skeleton width="30%" />
      <Skeleton variant="rounded" height={36} width="75%" />
      <Skeleton variant="rounded" height={160} />
      <Skeleton variant="rounded" height={140} />
    </Stack>
  );
}

/** Routed dialog: /catalog/exercises/:exerciseId on top of the exercise list. */
export function ExerciseDetailDialog() {
  const { t } = useTranslation(["catalog", "common"]);
  const { exerciseId } = useParams();
  const id = parseId(exerciseId);
  const navigate = useNavigate();
  const { search } = useLocation();
  const fullScreen = useMediaQuery((theme: Theme) => theme.breakpoints.down("sm"));
  const exercise = useExercise(id);

  // Keep the list filters when going back.
  const close = () => navigate({ pathname: "..", search });

  const notFound =
    id === null || (exercise.error instanceof ApiError && exercise.error.status === 404);

  let content;
  if (notFound) {
    content = (
      <EmptyState
        title={t("exercise.notFound")}
        description={t("exercise.notFoundBody")}
        action={<Button onClick={close}>{t("exercise.backToList")}</Button>}
      />
    );
  } else if (exercise.isError) {
    content = (
      <EmptyState
        title={t("exercise.loadError")}
        description={errorMessage(exercise.error)}
        action={<Button onClick={() => exercise.refetch()}>{t("common:actions.tryAgain")}</Button>}
      />
    );
  } else if (exercise.data) {
    content = <ExerciseDetailContent exercise={exercise.data} />;
  } else {
    content = <DetailSkeleton />;
  }

  return (
    <Dialog
      open
      onClose={close}
      fullScreen={fullScreen}
      fullWidth
      maxWidth="sm"
      aria-labelledby="exercise-title"
      slotProps={{ paper: { sx: { borderRadius: fullScreen ? 0 : 2 } } }}
    >
      <IconButton
        aria-label={t("common:actions.close")}
        onClick={close}
        sx={{ position: "absolute", top: 12, right: 12, zIndex: 1 }}
      >
        <CloseRounded />
      </IconButton>
      <DialogContent sx={{ px: { xs: 2.5, sm: 4 }, pt: { xs: 7, sm: 4 }, pb: 4 }}>
        {content}
      </DialogContent>
    </Dialog>
  );
}
