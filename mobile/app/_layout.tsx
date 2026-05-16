import { Stack } from "expo-router";
import { ActivityIndicator, View } from "react-native";
import { QueryClientProvider } from "@tanstack/react-query";

import { AuthProvider } from "@/providers/auth-provider";
import { ToastProvider } from "@/providers/toast-provider";
import { queryClient } from "@/lib/query";
import { colors } from "@/constants/theme";

function RootFallback() {
  return (
    <View style={{ flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: colors.canvas }}>
      <ActivityIndicator color={colors.brand} size="large" />
    </View>
  );
}

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <AuthProvider>
          <Stack screenOptions={{ headerShown: false }} />
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}
