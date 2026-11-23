/** The training profile as form state, and the request built from it. */
import type { ExperienceLevel, Profile, ProfileWrite } from "./api";

export type ProfileForm = {
  experience: ExperienceLevel | null;
  /** As typed - empty when not given. */
  weight: string;
  daysPerWeek: number;
  /** ISO weekdays, 1 = Monday. Empty - no preference. */
  weekdays: number[];
  minutes: number;
};

export const MIN_WEIGHT = 30;
export const MAX_WEIGHT = 300;

export const EMPTY_PROFILE: ProfileForm = {
  experience: null,
  weight: "",
  daysPerWeek: 3,
  weekdays: [],
  minutes: 60,
};

export function fromProfile(profile: Profile): ProfileForm {
  return {
    experience: profile.experience,
    weight: profile.weight_kg === null ? "" : String(profile.weight_kg),
    daysPerWeek: profile.days_per_week,
    weekdays: profile.preferred_weekdays ?? [],
    minutes: profile.max_session_minutes,
  };
}

/** Typed weight as a number; null when empty, NaN when invalid. */
export function parseWeight(text: string): number | null {
  const trimmed = text.trim().replace(",", ".");
  if (trimmed === "") return null;
  const value = Number(trimmed);
  return Number.isFinite(value) && value >= MIN_WEIGHT && value <= MAX_WEIGHT ? value : Number.NaN;
}

export function weightError(form: ProfileForm): boolean {
  return Number.isNaN(parseWeight(form.weight));
}

export function toProfileWrite(form: ProfileForm): ProfileWrite {
  if (form.experience === null) throw new Error("experience is required");
  return {
    experience: form.experience,
    weight_kg: parseWeight(form.weight),
    days_per_week: form.daysPerWeek,
    preferred_weekdays: form.weekdays.length > 0 ? [...form.weekdays].sort() : null,
    max_session_minutes: form.minutes,
  };
}
