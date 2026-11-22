import { useState } from "react";
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import AddRounded from "@mui/icons-material/AddRounded";
import DeleteOutlineRounded from "@mui/icons-material/DeleteOutlineRounded";
import DragIndicatorRounded from "@mui/icons-material/DragIndicatorRounded";
import LowPriorityRounded from "@mui/icons-material/LowPriorityRounded";
import MoreHorizRounded from "@mui/icons-material/MoreHorizRounded";
import {
  Alert,
  Box,
  Button,
  ButtonBase,
  Card,
  IconButton,
  Menu,
  MenuItem,
  Skeleton,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import type { ExerciseDetail } from "@/features/catalog/types";
import { useLocalizedName } from "@/i18n/useLocalized";
import { FONT_DISPLAY, FONT_MONO } from "@/styles/theme";
import { type DragData, sessionDropId } from "../dnd";
import type { DraftExercise, DraftSession } from "../draft";
import { useWeekdayName } from "../format";
import { orderHints, recommendedOrder } from "../insights";
import {MAX_EXERCISES_PER_SESSION, type PlanAssumptions} from "../types";
import { SetsStepper } from "./SetsStepper";
import {prescriptionFor} from "@/features/plan/prescription.ts";

export type SessionTime = {
  base: number;
  peak: number;
  peakWeek: number;
};

type SessionCardProps = {
  session: DraftSession;
  details: ReadonlyMap<number, ExerciseDetail>;
  time: SessionTime | undefined;
  dropTarget: boolean;
  onEdit: () => void;
  onRemove: () => void;
  onAddExercise: () => void;
  onShowExercise: (exerciseId: number) => void;
  onSetSets: (exerciseKey: string, sets: number) => void;
  onRemoveExercise: (exerciseKey: string) => void;
  onReorder: (orderedKeys: string[]) => void;
  rir: number;
  assumptions: PlanAssumptions | undefined;
};

export function SessionCard({
  session,
  details,
  time,
  dropTarget,
  onEdit,
  onRemove,
  onAddExercise,
  onShowExercise,
  onSetSets,
  onRemoveExercise,
  onReorder,
  rir,
  assumptions
}: SessionCardProps) {
  const { t } = useTranslation("plans");
  const localizedName = useLocalizedName();
  const weekdayName = useWeekdayName();
  const [menuAnchor, setMenuAnchor] = useState<HTMLElement | null>(null);
  const { setNodeRef: setDropRef } = useDroppable({ id: sessionDropId(session.key) });

  const hints = orderHints(session, details);
  const nameOf = (exercise: DraftExercise) => {
    const detail = details.get(exercise.exerciseId);
    return detail ? localizedName(detail) : "";
  };
  const byKey = new Map(session.exercises.map((e) => [e.key, e]));
  const full = session.exercises.length >= MAX_EXERCISES_PER_SESSION;
  const titleId = `session-${session.key}`;

  const meta = [
    session.weekday ? weekdayName(session.weekday) : t("session.noWeekdayShort"),
    t("session.limitShort", { minutes: session.maxMinutes }),
  ]
    .join(" · ")
    .toUpperCase();

  return (
    <Card
      component="section"
      aria-labelledby={titleId}
      sx={{
        p: 2,
        minWidth: 0,
        borderColor: dropTarget ? "primary.main" : undefined,
        transition: "border-color 120ms",
      }}
    >
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", pb: 1 }}>
        <Stack spacing={0.25} sx={{ flex: 1, minWidth: 0 }}>
          <Typography
            id={titleId}
            component="h3"
            sx={{ fontFamily: FONT_DISPLAY, fontSize: 18, fontWeight: 600 }}
            noWrap
          >
            {session.name}
          </Typography>
          <Typography sx={{ fontFamily: FONT_MONO, fontSize: 11, color: "text.secondary" }}>
            {meta}
          </Typography>
        </Stack>
        {time && <SessionTimeBadge time={time} limit={session.maxMinutes} />}
        <IconButton
          aria-label={t("session.menu", { session: session.name })}
          aria-haspopup="menu"
          onClick={(e) => setMenuAnchor(e.currentTarget)}
        >
          <MoreHorizRounded />
        </IconButton>
        <Menu anchorEl={menuAnchor} open={menuAnchor !== null} onClose={() => setMenuAnchor(null)}>
          <MenuItem
            onClick={() => {
              setMenuAnchor(null);
              onEdit();
            }}
          >
            {t("session.settings")}
          </MenuItem>
          <MenuItem
            onClick={() => {
              setMenuAnchor(null);
              onRemove();
            }}
            sx={{ color: "error.main" }}
          >
            {t("session.remove")}
          </MenuItem>
        </Menu>
      </Stack>

      <SortableContext
        items={session.exercises.map((e) => e.key)}
        strategy={verticalListSortingStrategy}
      >
        <Box
          ref={setDropRef}
          component="ul"
          aria-label={t("session.exercises", { session: session.name })}
          sx={{
            m: 0,
            p: 0,
            listStyle: "none",
            borderTop: 1,
            borderColor: "divider",
            minHeight: 56,
          }}
        >
          {session.exercises.length === 0 ? (
            <Typography
              component="li"
              variant="body2"
              color="text.secondary"
              sx={{ py: 2, textAlign: "center" }}
            >
              {t("session.empty")}
            </Typography>
          ) : (
            session.exercises.map((exercise) => (
              <ExerciseLine
                key={exercise.key}
                sessionKey={session.key}
                exercise={exercise}
                detail={details.get(exercise.exerciseId)}
                onShow={() => onShowExercise(exercise.exerciseId)}
                onSetSets={(sets) => onSetSets(exercise.key, sets)}
                onRemove={() => onRemoveExercise(exercise.key)}
                rir={rir}
                assumptions={assumptions}
              />
            ))
          )}
        </Box>
      </SortableContext>

      {hints.length > 0 && (
        <Alert
          severity="info"
          icon={<LowPriorityRounded fontSize="small" />}
          sx={{ mt: 1.5, borderRadius: 1 }}
        >
          {t("order.hint", {
            isolation: nameOf(byKey.get(hints[0].isolationKey)!),
            compound: nameOf(byKey.get(hints[0].compoundKey)!),
          })}
          <Box sx={{ pt: 0.75 }}>
            <Button
              color="inherit"
              size="small"
              variant="outlined"
              onClick={() => onReorder(recommendedOrder(session, details))}
            >
              {t("order.fix")}
            </Button>
          </Box>
        </Alert>
      )}

      <Button
        fullWidth
        startIcon={<AddRounded />}
        onClick={onAddExercise}
        disabled={full}
        sx={{ mt: 1.5, border: "1.5px dashed", borderColor: "divider" }}
      >
        {full ? t("session.full") : t("session.addExercise")}
      </Button>
    </Card>
  );
}

/** Week-1 minutes, plus the peak week when progression makes the session longer. */
export function SessionTimeBadge({ time, limit }: { time: SessionTime; limit: number }) {
  const { t } = useTranslation("plans");
  const base = Math.round(time.base);
  const peak = Math.round(time.peak);
  const over = peak > limit;

  return (
    <Tooltip
      title={t("session.timeHint", { base, peak, week: time.peakWeek, limit })}
      describeChild
    >
      <Stack
        direction="row"
        spacing={0.5}
        sx={{
          alignItems: "center",
          fontFamily: FONT_MONO,
          fontSize: 12,
          px: 1,
          py: 0.5,
          borderRadius: 1,
          bgcolor: over ? "warning.light" : "primary.light",
          color: over ? "warning.dark" : "primary.dark",
          flexShrink: 0,
        }}
      >
        <span>{t("session.minutes", { minutes: base })}</span>
        {peak !== base && <span>{t("session.peakMinutes", { minutes: peak })}</span>}
      </Stack>
    </Tooltip>
  );
}

type ExerciseLineProps = {
  sessionKey: string;
  exercise: DraftExercise;
  detail: ExerciseDetail | undefined;
  onShow: () => void;
  onSetSets: (sets: number) => void;
  onRemove: () => void;
  rir: number;
  assumptions: PlanAssumptions | undefined;
};

function ExerciseLine({
  sessionKey,
  exercise,
  detail,
  onShow,
  onSetSets,
  onRemove,
  rir,
  assumptions
}: ExerciseLineProps) {
  const { t } = useTranslation(["plans", "catalog"]);
  const localizedName = useLocalizedName();
  const name = detail ? localizedName(detail) : "";
  const prescription = detail && assumptions ? prescriptionFor(detail, assumptions) : undefined;
  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: exercise.key, data: { sessionKey } satisfies DragData });

  return (
    <Stack
      ref={setNodeRef}
      component="li"
      direction="row"
      spacing={0.5}
      sx={{
        alignItems: "center",
        py: 1,
        borderBottom: 1,
        borderColor: "divider",
        bgcolor: "background.paper",
        position: "relative",
        opacity: isDragging ? 0.4 : 1,
        transform: CSS.Translate.toString(transform),
        transition,
      }}
    >
      <IconButton
        ref={setActivatorNodeRef}
        size="small"
        aria-label={t("editor.dragHandle", { exercise: name })}
        sx={{ cursor: "grab", touchAction: "none", color: "text.secondary", ml: -1 }}
        {...attributes}
        {...listeners}
      >
        <DragIndicatorRounded fontSize="small" />
      </IconButton>
      <ButtonBase
        onClick={onShow}
        disabled={!detail}
        aria-label={t("editor.showExercise", { exercise: name })}
        sx={{
          flex: 1,
          minWidth: 0,
          display: "block",
          textAlign: "left",
          borderRadius: 1,
          px: 0.5,
          "&:hover .exercise-name": { textDecoration: "underline" },
        }}
      >
        {detail ? (
          <>
            <Typography className="exercise-name" sx={{ fontWeight: 500, fontSize: 14 }} noWrap>
              {name}
            </Typography>
            <Typography variant="caption" color="text.secondary" noWrap component="p">
              {t(`catalog:muscleGroups.${detail.main_group}`)} ·{" "}
              {t(detail.is_compound ? "catalog:exercise.compound" : "catalog:exercise.isolation")}
            </Typography>
            <Typography
              noWrap
              component="p"
              sx={{ fontFamily: FONT_MONO, fontSize: 11, color: "text.secondary" }}
            >
              {[
                prescription &&
                  t("prescription.reps", {
                    min: prescription.repRange[0],
                    max: prescription.repRange[1],
                  }),
                t("prescription.rir", { rir }),
              ]
                .filter(Boolean)
                .join(" · ")}
            </Typography>
          </>
        ) : (
          <>
            <Skeleton width="70%" />
            <Skeleton width="40%" />
          </>
        )}
      </ButtonBase>
      <SetsStepper value={exercise.sets} label={name} onChange={onSetSets} />
      <IconButton
        size="small"
        aria-label={t("editor.removeExerciseNamed", { exercise: name })}
        onClick={onRemove}
        sx={{ color: "text.secondary", "&:hover": { color: "error.main" } }}
      >
        <DeleteOutlineRounded fontSize="small" />
      </IconButton>
    </Stack>
  );
}

/** The dragged exercise following the pointer, outside of any list. */
export function ExerciseDragPreview({ detail }: { detail: ExerciseDetail | undefined }) {
  const localizedName = useLocalizedName();
  return (
    <Stack
      direction="row"
      spacing={1}
      sx={{
        alignItems: "center",
        px: 1.5,
        py: 1,
        bgcolor: "background.paper",
        border: 1,
        borderColor: "primary.main",
        borderRadius: 1,
        boxShadow: 4,
        cursor: "grabbing",
      }}
    >
      <DragIndicatorRounded fontSize="small" sx={{ color: "text.secondary" }} />
      <Typography sx={{ fontWeight: 500, fontSize: 14 }} noWrap>
        {detail ? localizedName(detail) : "…"}
      </Typography>
    </Stack>
  );
}