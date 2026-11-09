import i18n from "@/i18n";
import { en } from "@/i18n/locales/en";
import { notifySessionExpired, session } from "@/lib/session";

const BASE_URL = "/api/v1";
const NO_REFRESH_PATHS = ["/auth/login", "/auth/register", "/auth/refresh", "/auth/logout"];

export type TokenResponse = {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
};

export class ApiError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly detail: unknown;

  constructor(status: number, code: string | null, detail: unknown) {
    super(typeof detail === "string" ? detail : `Request failed with status ${status}`);
    this.status = status;
    this.code = code;
    this.detail = detail;
  }
}

function send(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = session.getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (typeof init.body === "string") headers.set("Content-Type", "application/json");
  return fetch(`${BASE_URL}${path}`, {
    ...init,
    headers,
    credentials: "same-origin",
  });
}

async function requestNewAccessToken(): Promise<boolean> {
  const response = await fetch(`${BASE_URL}/auth/refresh`, {
    method: "POST",
    credentials: "same-origin",
  });
  if (!response.ok) return false;
  const tokens = (await response.json()) as TokenResponse;
  session.setAccessToken(tokens.access_token);
  return true;
}

let refreshInFlight: Promise<boolean> | null = null;

/**
 * One refresh at a time - inside the tab (shared promise) and across tabs (Web Lock).
 * The backend revokes ALL sessions when a rotated refresh token is reused, so two
 * parallel refreshes with the same cookie would log the user out everywhere.
 */
export function refreshSession(): Promise<boolean> {
  refreshInFlight ??= (
    "locks" in navigator
      ? navigator.locks.request("loxofit-refresh", requestNewAccessToken)
      : requestNewAccessToken()
  )
    .catch(() => false)
    .finally(() => {
      refreshInFlight = null;
    });
  return refreshInFlight;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response = await send(path, init);

  if (response.status === 401 && !NO_REFRESH_PATHS.includes(path)) {
    const hadSession = session.getAccessToken() !== null;
    if (await refreshSession()) {
      response = await send(path, init);
    } else if (hadSession) {
      session.clear();
      notifySessionExpired();
    }
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, body?.code ?? null, body?.detail ?? body);
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}

const json = (body: unknown) => (body === undefined ? undefined : JSON.stringify(body));

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body: json(body) }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: "PUT", body: json(body) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: json(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  /** application/x-www-form-urlencoded - the OAuth2 login form */
  postForm: <T>(path: string, form: Record<string, string>) =>
    request<T>(path, { method: "POST", body: new URLSearchParams(form) }),
};

type ValidationIssue = { loc: (string | number)[]; msg: string };

/** FastAPI 422 -> { field: message } */
export function getFieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError) || error.status !== 422 || !Array.isArray(error.detail)) {
    return {};
  }
  const errors: Record<string, string> = {};
  for (const issue of error.detail as ValidationIssue[]) {
    const field = issue.loc.at(-1);
    if (typeof field === "string" && !(field in errors)) {
      errors[field] = issue.msg.replace(/^Value error, /, "");
    }
  }
  return errors;
}

type KnownErrorCode = keyof typeof en.common.errorCodes;

function isKnownErrorCode(code: string | null): code is KnownErrorCode {
  return code !== null && code in en.common.errorCodes;
}

/** User-facing message: a translated backend `code` when we know it, otherwise a generic one. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (isKnownErrorCode(error.code)) return i18n.t(`errorCodes.${error.code}`);
    return error.status >= 500 ? i18n.t("errors.server") : i18n.t("errors.requestFailed");
  }
  if (error instanceof TypeError) return i18n.t("errors.network");
  return i18n.t("errors.generic");
}
