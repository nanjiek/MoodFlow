import { Pressable, StyleSheet, Text } from "react-native";

import { colors, radius, spacing, typography } from "@/constants/theme";

export function Chip({
  label,
  selected,
  onPress,
}: {
  label: string;
  selected?: boolean;
  onPress?: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      style={[styles.chip, selected ? styles.selected : null]}
    >
      <Text style={[styles.text, selected ? styles.selectedText : null]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: {
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surfaceMuted,
  },
  selected: {
    backgroundColor: "#F7DCC7",
  },
  text: {
    color: colors.inkMuted,
    fontSize: typography.caption,
    fontWeight: "700",
  },
  selectedText: {
    color: colors.brandDeep,
  },
});
