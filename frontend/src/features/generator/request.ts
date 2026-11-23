/**
 * The generator form as plain data, and the request built from it.
 * Pure functions - no React - so they are easy to test.
 */
import type { Profile } from "@/features/profile/api";
import type { Focus, GenerationRequest, SplitTemplate } from "./types";

export type FormSession = {
  key: string;
  /** Empty - named after the focus ("Upper A"). */
  name: string;
  weekday: number | null;
  maxMinutes: number;
  /** Used by the custom template only. */
  focus: Focus;
};

export type GeneratorForm = {
  template: SplitTemplate;
  sessions: FormSession[];
  numWeeks: number;
};

export const DEFAULT_WEEKS = 5;
export const DEFAULT_MINUTES = 60;

/** Sessions per week when there is no profile. */
const DEFAULT_SESSIONS: Record<SplitTemplate, number> = {
  full_body: 3,
  upper_lower: 4,
  push_pull_legs: 3,
  custom: 3,
};

/** Mirrors the backend's template cycles (app/engine/focus.py). */
const TEMPLATE_CYCLE: Record<Exclude<SplitTemplate, "custom">, Focus[]> = {
  full_body: ["full_body"],
  upper_lower: ["upper", "lower"],
  push_pull_legs: ["push", "pull", "lower"],
};

const newKey = () => crypto.randomUUID();

/** Focus of every session: the template's cycle repeated, e.g. U, L, U, L. */
export function focuses(form: GeneratorForm): Focus[] {
  if (form.template === "custom") return form.sessions.map((s) => s.focus);
  const cycle = TEMPLATE_CYCLE[form.template];
  return form.sessions.map((_, i) => cycle[i % cycle.length]);
}

/**
 * Letter of every session whose focus repeats ("A", "B"), null otherwise -
 * the same naming as the backend, so the names match what gets saved.
 */
export function focusLetters(sessionFocuses: Focus[]): (string | null)[] {
  const total = new Map<Focus, number>();
  sessionFocuses.forEach((f) => total.set(f, (total.get(f) ?? 0) + 1));
  const seen = new Map<Focus, number>();
  return sessionFocuses.map((f) => {
    const n = (seen.get(f) ?? 0) + 1;
    seen.set(f, n);
    return (total.get(f) ?? 0) > 1 ? String.fromCharCode(64 + n) : null;
  });
}

function newSession(weekday: number | null, maxMinutes: number, focus: Focus): FormSession {
  return { key: newKey(), name: "", weekday, maxMinutes, focus };
}

/** Start from the profile: days per week, preferred days and the session limit. */
export function initialForm(profile: Profile | null | undefined): GeneratorForm {
  const template: SplitTemplate = "full_body";
  const count = profile?.days_per_week ?? DEFAULT_SESSIONS[template];
  const days = profile?.preferred_weekdays ?? [];
  const minutes = profile?.max_session_minutes ?? DEFAULT_MINUTES;
  return {
    template,
    numWeeks: DEFAULT_WEEKS,
    sessions: Array.from({ length: count }, (_, i) =>
      newSession(days[i] ?? null, minutes, "full_body"),
    ),
  };
}

/** Back from a run's request - "change parameters" starts from what was generated. */
export function fromRequest(request: GenerationRequest): GeneratorForm {
  return {
    template: request.template,
    numWeeks: request.num_weeks,
    sessions: request.sessions.map((s) => ({
      key: newKey(),
      name: s.name ?? "",
      weekday: s.weekday,
      maxMinutes: s.max_minutes,
      focus: s.focus ?? "full_body",
    })),
  };
}

/** A new session copies the last one's limit; the custom focus continues the cycle. */
export function setSessionCount(form: GeneratorForm, count: number): GeneratorForm {
  if (count <= form.sessions.length) return { ...form, sessions: form.sessions.slice(0, count) };
  const last = form.sessions.at(-1);
  const minutes = last?.maxMinutes ?? DEFAULT_MINUTES;
  const added = Array.from({ length: count - form.sessions.length }, () =>
    newSession(null, minutes, last?.focus ?? "full_body"),
  );
  return { ...form, sessions: [...form.sessions, ...added] };
}

/**
 * Switching to "custom" keeps the focuses the template gave, so the user edits
 * from there instead of from all "full body".
 */
export function setTemplate(form: GeneratorForm, template: SplitTemplate): GeneratorForm {
  const current = focuses(form);
  return {
    ...form,
    template,
    sessions:
      template === "custom"
        ? form.sessions.map((s, i) => ({ ...s, focus: current[i] }))
        : form.sessions,
  };
}

export function updateSession(
  form: GeneratorForm,
  key: string,
  change: Partial<Omit<FormSession, "key">>,
): GeneratorForm {
  return {
    ...form,
    sessions: form.sessions.map((s) => (s.key === key ? { ...s, ...change } : s)),
  };
}

/**
 * The request. `names` are the localized default names - the backend names
 * sessions in English, the user should see them in their language.
 */
export function toRequest(form: GeneratorForm, names: string[]): GenerationRequest {
  const custom = form.template === "custom";
  return {
    template: form.template,
    num_weeks: form.numWeeks,
    targets: [],
    seed: null,
    sessions: form.sessions.map((s, i) => ({
      name: s.name.trim() || names[i],
      weekday: s.weekday,
      max_minutes: s.maxMinutes,
      focus: custom ? s.focus : null,
    })),
  };
}
