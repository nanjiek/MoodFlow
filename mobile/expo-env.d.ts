/// <reference types="expo-router/types" />

declare namespace NodeJS {
  interface ProcessEnv {
    EXPO_PUBLIC_API_BASE_URL?: string;
    EXPO_PUBLIC_MODEL_BASE_URL?: string;
  }
}
