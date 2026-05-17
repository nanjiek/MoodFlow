import Constants from "expo-constants";
import { Platform } from "react-native";

const DEFAULT_API_PORT = "8000";
const DEFAULT_MODEL_PORT = "8010";
const LOCALHOST_API_BASE_URL = `http://localhost:${DEFAULT_API_PORT}`;

function stripTrailingSlash(value: string) {
  return value.replace(/\/+$/, "");
}

function normalizeBaseUrl(value?: string | null) {
  if (!value) {
    return "";
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return "";
  }

  if (/^https?:\/\//i.test(trimmed)) {
    return stripTrailingSlash(trimmed);
  }

  return stripTrailingSlash(`http://${trimmed}`);
}

function extractHost(value?: string | null) {
  if (!value) {
    return "";
  }

  try {
    const normalized = /^https?:\/\//i.test(value) ? value : `http://${value}`;
    return new URL(normalized).hostname;
  } catch {
    return "";
  }
}

function getExpoHost() {
  const hostCandidates = [
    Constants.expoConfig?.hostUri,
    (Constants as typeof Constants & {
      manifest2?: { extra?: { expoClient?: { hostUri?: string } } };
    }).manifest2?.extra?.expoClient?.hostUri,
    Constants.linkingUri,
  ];

  for (const candidate of hostCandidates) {
    const host = extractHost(candidate);
    if (host && host !== "localhost" && host !== "127.0.0.1") {
      return host;
    }
  }

  return "";
}

function inferLanBaseUrl(port: string) {
  if (Platform.OS === "web") {
    return "";
  }

  const host = getExpoHost();
  if (!host) {
    return "";
  }

  return `http://${host}:${port}`;
}

function resolveApiBaseUrl() {
  return (
    normalizeBaseUrl(process.env.EXPO_PUBLIC_API_BASE_URL) ||
    inferLanBaseUrl(DEFAULT_API_PORT) ||
    LOCALHOST_API_BASE_URL
  );
}

function resolveModelBaseUrl() {
  return (
    normalizeBaseUrl(process.env.EXPO_PUBLIC_MODEL_BASE_URL) ||
    inferLanBaseUrl(DEFAULT_MODEL_PORT)
  );
}

export const env = {
  apiBaseUrl: resolveApiBaseUrl(),
  modelBaseUrl: resolveModelBaseUrl(),
};
