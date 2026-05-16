import { StyleSheet, View } from "react-native";

import { colors, radius, spacing } from "@/constants/theme";
import { BodyText, Subheading } from "@/components/ui/text";

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <View style={styles.box}>
      <Subheading>{title}</Subheading>
      <BodyText>{description}</BodyText>
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surfaceMuted,
    padding: spacing.lg,
    gap: spacing.xs,
  },
});
