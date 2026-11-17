import { useCallback } from "react";

import { useLanguage } from "@/i18n";

/** 2024-01-01 was a Monday, so day `n` of that week is ISO weekday `n`. */
const isoWeekday = (weekday: number) => new Date(2024, 0, weekday);

/** Localized weekday name for an ISO weekday (1 = Monday). */
export function useWeekdayName() {
  const language = useLanguage();
  return useCallback(
    (weekday: number, width: "short" | "long" = "short") =>
      isoWeekday(weekday).toLocaleDateString(language, { weekday: width }),
    [language],
  );
}

/** "3 Nov 2026" in the UI language. */
export function useFormatDate() {
  const language = useLanguage();
  return useCallback(
    (iso: string) =>
      new Date(iso).toLocaleDateString(language, {
        day: "numeric",
        month: "short",
        year: "numeric",
      }),
    [language],
  );
}

export function formatTempo(tempo: string): string {
  return tempo.split("").join("-");
}