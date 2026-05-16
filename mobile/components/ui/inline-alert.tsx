import { StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "@/constants/theme";

export function InlineAlert({
  message,
  tone = "info",
}: {
  message: string;
  tone?: "info" | "warning" | "danger";
}) {
  const palette =
    tone === "danger"
      ? { bg: "#FDE8E8", fg: colors.danger }
      : tone === "warning"
        ? { bg: "#FFF2DF", fg: colors.warning }
        : { bg: "#EEF4FA", fg: "#37566F" };

  return (
    <View style={[styles.box, { backgroundColor: palette.bg }]}>
      <Text style={[styles.text, { color: palette.fg }]}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    borderRadius: radius.md,
    padding: spacing.md,
  },
  text: {
    fontSize: typography.caption,
    fontWeight: "600",
  },
});
