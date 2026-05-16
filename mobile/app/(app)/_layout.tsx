import { Redirect, Stack } from "expo-router";

import { useAuth } from "@/hooks/useAuth";

export default function AppLayout() {
  const { status, bootstrapComplete } = useAuth();

  if (!bootstrapComplete) {
    return null;
  }

  if (status !== "authenticated") {
    return <Redirect href="/(auth)/login" />;
  }

  return <Stack screenOptions={{ headerShown: false }} />;
}
