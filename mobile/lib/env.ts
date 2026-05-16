const fallbackBaseUrl = "http://localhost:8000";

export const env = {
  apiBaseUrl: process.env.EXPO_PUBLIC_API_BASE_URL ?? fallbackBaseUrl,
  modelBaseUrl: process.env.EXPO_PUBLIC_MODEL_BASE_URL ?? "",
};
