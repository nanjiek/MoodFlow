import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "@/constants/theme";

export function MenuRow({
  title,
  subtitle,
  onPress,
}: {
  title: string;
  subtitle?: string;
  onPress?: () => void;
}) {
  return (
    <Pressable onPress={onPress} style={styles.row}>
      <View style={styles.texts}>
        <Text style={styles.title}>{title}</Text>
        {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
      </View>
      <Text style={styles.arrow}>›</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    minHeight: 62,
    backgroundColor: colors.surface,
    borderRadius: 18,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  texts: {
    flex: 1,
    gap: 4,
  },
  title: {
    color: colors.ink,
    fontSize: typography.body,
    fontWeight: "700",
  },
  subtitle: {
    color: colors.inkSoft,
    fontSize: typography.caption,
  },
  arrow: {
    color: colors.inkSoft,
    fontSize: 24,
  },
});
