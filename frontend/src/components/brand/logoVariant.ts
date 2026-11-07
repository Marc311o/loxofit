import { useSyncExternalStore } from "react";
import {
  DEFAULT_LOGO_VARIANT,
  LOGO_VARIANTS,
  type LogoVariant,
} from "./logoMarks.tsx";

const STORAGE_KEY = "loxofit.logoVariant";
const listeners = new Set<() => void>();

function isLogoVariant(value: unknown): value is LogoVariant {
  return (
    typeof value === "string" &&
    (LOGO_VARIANTS as readonly string[]).includes(value)
  );
}

function readInitialVariant(): LogoVariant {
  // Variant switching is a development aid; production always uses the default mark.
  if (!import.meta.env.DEV || typeof window === "undefined")
    return DEFAULT_LOGO_VARIANT;

  const fromUrl = new URLSearchParams(window.location.search)
    .get("logo")
    ?.toUpperCase();
  if (isLogoVariant(fromUrl)) return fromUrl;

  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (isLogoVariant(stored)) return stored;
  } catch {
    // Storage unavailable (private mode, blocked cookies) – fall back to default.
  }
  return DEFAULT_LOGO_VARIANT;
}

let currentVariant = readInitialVariant();

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot(): LogoVariant {
  return currentVariant;
}

export function setLogoVariant(variant: LogoVariant): void {
  currentVariant = variant;
  try {
    window.localStorage.setItem(STORAGE_KEY, variant);
  } catch {
    // Storage unavailable – keep the choice in memory only.
  }
  listeners.forEach((listener) => listener());
}

export function useLogoVariant(): LogoVariant {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
