import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { errorMessage } from "@/lib/api";
import { toast } from "@/lib/toast";
import { planKeys, saveBaseWeek } from "./api";
import { applyServerIds, type Draft, fromWeek, toWrite } from "./draft";
import type { PlanDetail } from "./types";

export type SaveStatus = "saved" | "pending" | "saving" | "error";

const SAVE_DELAY_MS = 700;

/**
 * The editable base week with autosave.
 *
 * Edits go to a local draft right away and are saved after a short pause, one
 * request at a time. `null` draft = not edited yet, the server copy is shown.
 * Once edited, the local draft stays: it keeps the keys of new sessions and
 * exercises stable (dialogs hold on to them), and only the ids the server
 * assigned are copied onto it after each save.
 */
export function useBaseWeekDraft(plan: PlanDetail) {
  const queryClient = useQueryClient();
  const server = useMemo(() => fromWeek(plan.weeks[0]), [plan]);

  const [draft, setDraft] = useState<Draft | null>(null);
  const [status, setStatus] = useState<SaveStatus>("saved");

  // Read from timers and request callbacks, so they live in refs.
  const latest = useRef<Draft | null>(null);
  const version = useRef(0);
  const savedVersion = useRef(0);
  const timer = useRef<number | undefined>(undefined);
  const inFlight = useRef(false);

  // One request at a time: edits made while it runs are picked up by the loop.
  const save = useCallback(async () => {
    window.clearTimeout(timer.current);
    timer.current = undefined;
    if (inFlight.current) return;

    inFlight.current = true;
    try {
      while (latest.current !== null && version.current !== savedVersion.current) {
        const sent = latest.current;
        const sentVersion = version.current;
        setStatus("saving");
        try {
          const saved = await saveBaseWeek(plan.id, toWrite(sent));
          queryClient.setQueryData(planKeys.detail(plan.id), saved);
          void queryClient.invalidateQueries({ queryKey: planKeys.analysis(plan.id) });
          void queryClient.invalidateQueries({ queryKey: planKeys.list() });
          void queryClient.invalidateQueries({ queryKey: planKeys.active() });

          savedVersion.current = sentVersion;
          latest.current = applyServerIds(latest.current ?? sent, sent, saved);
          setDraft(latest.current);
          if (version.current === sentVersion) setStatus("saved");
        } catch (error) {
          setStatus("error");
          toast.error(errorMessage(error));
          return;
        }
      }
    } finally {
      inFlight.current = false;
    }
  }, [plan.id, queryClient]);

  const edit = useCallback(
    (change: (draft: Draft) => Draft) => {
      const next = change(latest.current ?? server);
      latest.current = next;
      version.current += 1;
      setDraft(next);
      setStatus("pending");
      window.clearTimeout(timer.current);
      timer.current = window.setTimeout(() => void save(), SAVE_DELAY_MS);
    },
    [save, server],
  );

  // Leaving the editor: save what is waiting instead of dropping it.
  useEffect(
    () => () => {
      if (timer.current !== undefined) void save();
    },
    [save],
  );

  // Closing the tab with unsaved edits: let the browser ask.
  const unsaved = status === "pending" || status === "saving" || status === "error";
  useEffect(() => {
    if (!unsaved) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [unsaved]);

  return {
    draft: draft ?? server,
    status,
    edit,
    retry: save,
  };
}
