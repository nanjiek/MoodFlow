import { ActivityIndicator, Pressable, StyleSheet, Text } from "react-native";

import { colors, radius, spacing, typography } from "@/constants/theme";

export function Button({
  title,
  onPress,
  tone = "primary",
  disabled,
  loading,
}: {
  title: string;
  onPress?: () => void;
  tone?: "primary" | "ghost" | "soft" | "danger";
  disabled?: boolean;
  loading?: boolean;
}) {
  const backgroundColor =
    tone === "primary" ? colors.brand : tone === "danger" ? colors.danger : tone === "soft" ? "#FDE7D7" : "transparent";
  const textColor = tone === "ghost" ? colors.ink : tone === "soft" ? colors.brandDeep : colors.surface;
  const borderColor = tone === "ghost" ? colors.line : "transparent";

  return (
    <Pressable
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        {
          backgroundColor,
          borderColor,
          opacity: disabled ? 0.55 : pressed ? 0.85 : 1,
        },
      ]}
    >
      {loading ? <ActivityIndicator color={textColor} /> : <Text style={[styles.label, { color: textColor }]}>{title}</Text>}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 52,
    borderRadius: radius.pill,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.lg,
  },
  label: {
    fontSize: typography.body,
    fontWeight: "700",
  },
});
