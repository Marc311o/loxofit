import { useState } from "react";
import {
  closestCenter,
  type CollisionDetection,
  DndContext,
  type DragEndEvent,
  type DragOverEvent,
  DragOverlay,
  type DragStartEvent,
  KeyboardSensor,
  PointerSensor,
  pointerWithin,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import AddRounded from "@mui/icons-material/AddRounded";
import CloudDoneOutlined from "@mui/icons-material/CloudDoneOutlined";
import ErrorOutlineRounded from "@mui/icons-material/ErrorOutlineRounded";
import { Alert, Box, Button, CircularProgress, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { ConfirmDialog } from "@/components/ConfirmDialog";
import { EmptyState } from "@/components/EmptyState";
import { useMuscles } from "@/features/catalog/muscles/api";
import type { MuscleGroup } from "@/features/catalog/types";
import { toast } from "@/lib/toast";
import { useGenerateProgression, usePlanAnalysis } from "../api";
import { AnalysisPanel } from "../components/AnalysisPanel";
import { ExercisePickerDialog } from "../components/ExercisePickerDialog";
import { ExerciseInfoDialog } from "../components/ExerciseInfoDialog";
import { ExerciseDragPreview, SessionCard, type SessionTime } from "../components/SessionCard";
import { SessionSettingsDialog } from "../components/SessionSettingsDialog";
import { WeekView } from "../components/WeekView";
import {
  addExercise,
  addSession,
  DEFAULT_MAX_MINUTES,
  type DraftSession,
  hasExercises,
  removeExercise,
  removeSession,
  reorderExercises,
  setSets,
  updateSession,
} from "../draft";
import { applyDrop, type DragData, targetSession } from "../dnd";
import { peakWeek } from "../insights";
import { usePlanOutlet } from "../planOutlet";
import { MAX_SESSIONS_PER_WEEK, type PlanDetail } from "../types";
import { type SaveStatus, useBaseWeekDraft } from "../useBaseWeekDraft";
import { useExerciseDetails } from "../useExerciseDetails";

type Dialog =
  | { kind: "newSession" }
  | { kind: "editSession"; session: DraftSession }
  | { kind: "removeSession"; session: DraftSession }
  | { kind: "pick"; session: DraftSession }
  | { kind: "info"; exerciseId: number };

/** Pointer first (precise across sessions), nearest item as the fallback - also for keyboard. */
const collision: CollisionDetection = (args) => {
  const hits = pointerWithin(args);
  return hits.length > 0 ? hits : closestCenter(args);
};

export function BaseWeekPage() {
  const { plan } = usePlanOutlet();
  return plan.status === "archived" ? (
    <ArchivedBaseWeek plan={plan} />
  ) : (
    <BaseWeekEditor key={plan.id} plan={plan} />
  );
}

function ArchivedBaseWeek({ plan }: { plan: PlanDetail }) {
  const { t } = useTranslation("plans");
  const base = plan.weeks[0];
  const analysis = usePlanAnalysis(plan.id);
  const { details } = useExerciseDetails(
    base?.sessions.flatMap((s) => s.exercises.map((e) => e.exercise_id)) ?? [],
  );
  return (
    <Stack spacing={2}>
      <Alert severity="info">{t("editor.archived")}</Alert>
      {base && <WeekView week={base} details={details} assumptions={analysis.data?.assumptions} />}
    </Stack>
  );
}

function BaseWeekEditor({ plan }: { plan: PlanDetail }) {
  const { t } = useTranslation("plans");
  const { draft, status, edit, retry } = useBaseWeekDraft(plan);
  const analysis = usePlanAnalysis(plan.id);
  const generate = useGenerateProgression(plan.id);
  const muscles = useMuscles();
  const { details } = useExerciseDetails(
    draft.sessions.flatMap((s) => s.exercises.map((e) => e.exerciseId)),
  );
  const [dialog, setDialog] = useState<Dialog | null>(null);
  const close = () => setDialog(null);

  const saved = plan.weeks[0]?.sessions ?? [];
  const savedIndex = new Map(saved.map((s, i) => [s.id, i]));
  const peak = analysis.data ? peakWeek(analysis.data) : undefined;
  const firstWeek = analysis.data?.weeks[0];
  const timeOf = (session: DraftSession): SessionTime | undefined => {
    const index = session.id === undefined ? undefined : savedIndex.get(session.id);
    if (index === undefined || !firstWeek || !peak) return undefined;
    return {
      base: firstWeek.session_minutes[index],
      peak: peak.session_minutes[index],
      peakWeek: peak.week_number,
    };
  };

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );
  const [dragged, setDragged] = useState<{ key: string; exerciseId: number } | null>(null);
  const [overSession, setOverSession] = useState<string | null>(null);

  const handleDragStart = ({ active }: DragStartEvent) => {
    const key = String(active.id);
    const exercise = draft.sessions.flatMap((s) => s.exercises).find((e) => e.key === key);
    setDragged(exercise ? { key, exerciseId: exercise.exerciseId } : null);
  };
  const handleDragOver = ({ over }: DragOverEvent) =>
    setOverSession(over ? (targetSession(String(over.id), over.data.current) ?? null) : null);
  const handleDragEnd = ({ active, over }: DragEndEvent) => {
    setDragged(null);
    setOverSession(null);
    if (!over) return;
    const from = (active.data.current as DragData | undefined)?.sessionKey;
    const to = targetSession(String(over.id), over.data.current);
    if (!from || !to) return;
    const args = [String(active.id), from, String(over.id), to] as const;
    const result = applyDrop(draft, ...args);
    if (result === null) return;
    if ("refused" in result) {
      toast.info(t("editor.cannotMove"));
      return;
    }
    edit((d) => {
      const next = applyDrop(d, ...args);
      return next && "draft" in next ? next.draft : d;
    });
  };

  const lacking = new Set<MuscleGroup>();
  peak?.muscles
    .filter((m) => m.zone === "below_mev" && m.priority > 0)
    .forEach((m) => {
      const group = muscles.data?.find((x) => x.id === m.muscle_id)?.muscle_group;
      if (group) lacking.add(group);
    });

  const takenWeekdays = (except?: string) =>
    new Set(
      draft.sessions.flatMap((s) => (s.key !== except && s.weekday !== null ? [s.weekday] : [])),
    );

  const canGenerate = hasExercises(draft) && status === "saved";
  const updating = status !== "saved" || analysis.isFetching;

  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: { xs: "1fr", lg: "minmax(0, 1fr) 340px" },
        gap: 2.5,
        alignItems: "start",
      }}
    >
      <Stack spacing={2} sx={{ minWidth: 0 }}>
        <Stack
          direction="row"
          sx={{ alignItems: "center", justifyContent: "space-between", gap: 2, flexWrap: "wrap" }}
        >
          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 560 }}>
            {t("editor.intro", { last: plan.num_weeks })}
          </Typography>
          <SaveIndicator status={status} onRetry={retry} />
        </Stack>

        {plan.weeks.length > 1 && (
          <Alert severity={plan.status === "active" ? "warning" : "info"}>
            {t(plan.status === "active" ? "editor.activeWarning" : "editor.generatedWarning", {
              last: plan.num_weeks,
            })}
          </Alert>
        )}

        {draft.sessions.length === 0 ? (
          <EmptyState
            title={t("editor.emptyTitle")}
            description={t("editor.emptyBody")}
            action={
              <Button
                variant="contained"
                startIcon={<AddRounded />}
                onClick={() => setDialog({ kind: "newSession" })}
              >
                {t("session.add")}
              </Button>
            }
          />
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={collision}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
            onDragCancel={() => {
              setDragged(null);
              setOverSession(null);
            }}
          >
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" },
                gap: 2,
                alignItems: "start",
              }}
            >
              {draft.sessions.map((session) => (
                <SessionCard
                  key={session.key}
                  session={session}
                  details={details}
                  time={timeOf(session)}
                  dropTarget={dragged !== null && overSession === session.key}
                  rir={plan.weeks[0]?.rir ?? 0}
                  assumptions={analysis.data?.assumptions}
                  onEdit={() => setDialog({ kind: "editSession", session })}
                  onRemove={() =>
                    session.exercises.length === 0
                      ? edit((d) => removeSession(d, session.key))
                      : setDialog({ kind: "removeSession", session })
                  }
                  onAddExercise={() => setDialog({ kind: "pick", session })}
                  onShowExercise={(exerciseId) => setDialog({ kind: "info", exerciseId })}
                  onSetSets={(key, sets) => edit((d) => setSets(d, session.key, key, sets))}
                  onRemoveExercise={(key) => edit((d) => removeExercise(d, session.key, key))}
                  onReorder={(keys) => edit((d) => reorderExercises(d, session.key, keys))}
                />
              ))}
              {draft.sessions.length < MAX_SESSIONS_PER_WEEK && (
                <Button
                  startIcon={<AddRounded />}
                  onClick={() => setDialog({ kind: "newSession" })}
                  sx={{
                    minHeight: 120,
                    border: "1.5px dashed",
                    borderColor: "divider",
                    borderRadius: 2,
                  }}
                >
                  {t("session.add")}
                </Button>
              )}
            </Box>
            <DragOverlay>
              {dragged && <ExerciseDragPreview detail={details.get(dragged.exerciseId)} />}
            </DragOverlay>
          </DndContext>
        )}
      </Stack>

      <Box sx={{ position: { lg: "sticky" }, top: { lg: 24 } }}>
        <AnalysisPanel
          analysis={analysis.data}
          updating={updating}
          sessionNames={saved.map((s) => s.name)}
          sessionLimits={saved.map((s) => s.max_minutes)}
          numWeeks={plan.num_weeks}
          canGenerate={canGenerate}
          generateHint={
            hasExercises(draft) ? t("editor.waitForSave") : t("editor.addExercisesFirst")
          }
          generating={generate.isPending}
          onGenerate={() =>
            generate.mutate(undefined, {
              onSuccess: () => toast.success(t("editor.weeksComputed", { last: plan.num_weeks })),
            })
          }
        />
      </Box>

      {dialog?.kind === "newSession" && (
        <SessionSettingsDialog
          title={t("session.addTitle")}
          initial={{
            name: t("session.defaultName", { number: draft.sessions.length + 1 }),
            weekday: null,
            maxMinutes: DEFAULT_MAX_MINUTES,
          }}
          takenWeekdays={takenWeekdays()}
          onClose={close}
          onSave={(settings) => {
            edit((d) => addSession(d, settings));
            close();
          }}
        />
      )}
      {dialog?.kind === "editSession" && (
        <SessionSettingsDialog
          title={t("session.settings")}
          initial={dialog.session}
          takenWeekdays={takenWeekdays(dialog.session.key)}
          onClose={close}
          onSave={(settings) => {
            edit((d) => updateSession(d, dialog.session.key, settings));
            close();
          }}
        />
      )}
      <ConfirmDialog
        open={dialog?.kind === "removeSession"}
        title={t("session.removeTitle", {
          session: dialog?.kind === "removeSession" ? dialog.session.name : "",
        })}
        description={t("session.removeBody")}
        confirmLabel={t("session.remove")}
        cancelLabel={t("actions.cancel")}
        destructive
        onCancel={close}
        onConfirm={() => {
          if (dialog?.kind === "removeSession") edit((d) => removeSession(d, dialog.session.key));
          close();
        }}
      />
      {dialog?.kind === "info" && (
        <ExerciseInfoDialog exerciseId={dialog.exerciseId} onClose={close} />
      )}
      {dialog?.kind === "pick" && (
        <ExercisePickerDialog
          sessionName={dialog.session.name}
          excludedIds={
            new Set(
              draft.sessions
                .find((s) => s.key === dialog.session.key)
                ?.exercises.map((e) => e.exerciseId),
            )
          }
          suggestedGroups={[...lacking]}
          onClose={close}
          onPick={(exerciseId) => {
            edit((d) => addExercise(d, dialog.session.key, exerciseId));
            close();
          }}
        />
      )}
    </Box>
  );
}

function SaveIndicator({ status, onRetry }: { status: SaveStatus; onRetry: () => void }) {
  const { t } = useTranslation("plans");

  if (status === "error") {
    return (
      <Stack
        direction="row"
        spacing={1}
        sx={{ alignItems: "center", color: "error.main" }}
        role="status"
      >
        <ErrorOutlineRounded fontSize="small" />
        <Typography variant="body2">{t("save.error")}</Typography>
        <Button size="small" onClick={onRetry}>
          {t("save.retry")}
        </Button>
      </Stack>
    );
  }
  return (
    <Stack
      direction="row"
      spacing={0.75}
      sx={{ alignItems: "center", color: "text.secondary" }}
      role="status"
      aria-live="polite"
    >
      {status === "saved" ? (
        <CloudDoneOutlined fontSize="small" />
      ) : (
        <CircularProgress size={14} color="inherit" />
      )}
      <Typography variant="body2">{t(`save.${status}`)}</Typography>
    </Stack>
  );
}