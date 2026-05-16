import type { AppBootstrapState } from "@/types/app";

export function useAppBootstrap(): AppBootstrapState {
  return {
    status: "ready"
  };
}
