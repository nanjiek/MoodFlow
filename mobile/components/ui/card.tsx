import { StyleSheet, View, type ViewProps } from "react-native";

import { colors, radius, shadows, spacing } from "@/constants/theme";

export function Card(props: ViewProps) {
  return <View {...props} style={[styles.card, props.style]} />;
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.md,
    gap: spacing.sm,
    ...shadows.card,
  },
});
