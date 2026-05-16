import { env } from "@/lib/env";
import { getStoredToken, setStoredProfile, setStoredToken } from "@/lib/storage";
import type { ApiSuccess, FieldErrorMap } from "@/types/api";
import { ApiError } from "@/types/api";

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

let onUnauthorized: null | (() => Promise<void> | void) = null;

export function registerUnauthorizedHandler(handler: typeof onUnauthorized) {
  onUnauthorized = handler;
}

function normalizeFieldErrors(data: unknown): FieldErrorMap | undefined {
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return undefined;
  }
  return data as FieldErrorMap;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}) {
  const token = await getStoredToken();
  const headers = new Headers(options.headers ?? {});
  headers.set("Accept", "application/json");
  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    ...options,
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  const rawText = await response.text();
  let payload: ApiSuccess<T> | Record<string, unknown> | null = null;

  try {
    payload = rawText ? JSON.parse(rawText) : null;
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const message =
      (payload && typeof payload === "object" && "message" in payload && typeof payload.message === "string"
        ? payload.message
        : `Request failed with status ${response.status}`) || "Request failed";
    const code = payload && typeof payload === "object" && "code" in payload ? payload.code : undefined;
    const fieldErrors =
      payload && typeof payload === "object" && "data" in payload ? normalizeFieldErrors(payload.data) : undefined;
    const error = new ApiError(message, response.status, code as number | string | undefined, fieldErrors);

    if (response.status === 401) {
      await setStoredToken(null);
      await setStoredProfile(null);
      await onUnauthorized?.();
    }
    throw error;
  }

  if (!payload || typeof payload !== "object" || !("data" in payload)) {
    throw new ApiError("Malformed API response.", response.status);
  }

  return payload as ApiSuccess<T>;
}
