import i18n from "i18next";
import { initReactI18next, useTranslation } from "react-i18next";

import { en } from "./locales/en";
import { pl } from "./locales/pl";

export const SUPPORTED_LANGUAGES = ["pl", "en"] as const;
export type Language = (typeof SUPPORTED_LANGUAGES)[number];

const FALLBACK_LANGUAGE: Language = "en";
const STORAGE_KEY = "loxofit.language";

function isLanguage(value: unknown): value is Language {
  return SUPPORTED_LANGUAGES.some((language) => language === value);
}

/** Saved choice first, then the browser's preferred languages, then English. */
function detectLanguage(): Language {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (isLanguage(stored)) return stored;
  } catch {
    // Storage unavailable - fall through to the browser settings.
  }
  for (const tag of navigator.languages ?? [navigator.language]) {
    const base = tag.toLowerCase().split("-")[0];
    if (isLanguage(base)) return base;
  }
  return FALLBACK_LANGUAGE;
}

void i18n.use(initReactI18next).init({
  resources: { en, pl },
  lng: detectLanguage(),
  fallbackLng: FALLBACK_LANGUAGE,
  supportedLngs: SUPPORTED_LANGUAGES,
  ns: Object.keys(en),
  defaultNS: "common",
  interpolation: { escapeValue: false }, // React escapes already
  initAsync: false, // resources are bundled - no loading state needed
});

document.documentElement.lang = i18n.language;

// Only explicit choices are remembered; the detected language is not saved.
i18n.on("languageChanged", (language) => {
  document.documentElement.lang = language;
  try {
    window.localStorage.setItem(STORAGE_KEY, language);
  } catch {
    // Storage unavailable - the choice lasts for this session only.
  }
});

export function changeLanguage(language: Language) {
  return i18n.changeLanguage(language);
}

/** Active UI language; re-renders the caller when it changes. */
export function useLanguage(): Language {
  const { i18n: instance } = useTranslation();
  return isLanguage(instance.resolvedLanguage) ? instance.resolvedLanguage : FALLBACK_LANGUAGE;
}

export default i18n;
