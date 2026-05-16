import { createContext, useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "@/constants/theme";

type ToastState = {
  visible: boolean;
  message: string;
  tone: "default" | "danger" | "success";
};

export const ToastContext = createContext({
  show: (_message: string, _tone: ToastState["tone"] = "default"): void => undefined,
});

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toast, setToast] = useState<ToastState>({ visible: false, message: "", tone: "default" });

  const value = useMemo(
    () => ({
      show: (message: string, tone: ToastState["tone"] = "default") => {
        setToast({ visible: true, message, tone });
      },
    }),
    [],
  );

  const backgroundColor =
    toast.tone === "danger" ? "#7D2D2D" : toast.tone === "success" ? "#275D47" : "#314158";

  return (
    <ToastContext.Provider value={value}>
      {children}
      {toast.visible ? (
        <Pressable style={styles.overlay} onPress={() => setToast((prev) => ({ ...prev, visible: false }))}>
          <View style={[styles.toast, { backgroundColor }]}>
            <Text style={styles.toastText}>{toast.message}</Text>
          </View>
        </Pressable>
      ) : null}
    </ToastContext.Provider>
  );
}

const styles = StyleSheet.create({
  overlay: {
    position: "absolute",
    left: spacing.md,
    right: spacing.md,
    bottom: spacing.xl,
    alignItems: "center",
  },
  toast: {
    width: "100%",
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
  },
  toastText: {
    color: colors.surface,
    fontSize: typography.body,
    fontWeight: "600",
  },
});
