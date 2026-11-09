import { useCallback } from "react";

import { useLanguage } from "./index";

type Named = { name_en: string; name_pl: string };

export function useLocalizedName() {
  const language = useLanguage();
  return useCallback(
    (item: Named) => (language === "pl" ? item.name_pl : item.name_en),
    [language],
  );
}

export function useFormatNumber() {
  const language = useLanguage();
  return useCallback(
    (value: number, fractionDigits?: number) =>
      value.toLocaleString(
        language,
        fractionDigits === undefined
          ? undefined
          : {
              minimumFractionDigits: fractionDigits,
              maximumFractionDigits: fractionDigits,
            },
      ),
    [language],
  );
}
