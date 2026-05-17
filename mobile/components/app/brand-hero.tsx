import { StyleSheet, View } from "react-native";

import { Card } from "@/components/ui/card";
import { BodyText, CaptionText, Heading } from "@/components/ui/text";
import { colors, radius, spacing } from "@/constants/theme";

export function BrandHero({
  eyebrow = "MoodFlow",
  title = "给情绪留一处可以慢慢回看的地方。",
  description = "记录当下感受，回看情绪变化，也给自己一点温和的回应。",
}: {
  eyebrow?: string;
  title?: string;
  description?: string;
}) {
  return (
    <Card style={styles.card}>
      <View style={styles.badge}>
        <CaptionText style={styles.badgeText}>{eyebrow}</CaptionText>
      </View>
      <Heading>{title}</Heading>
      <BodyText>{description}</BodyText>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#FFF7F0",
    borderRadius: radius.lg,
    gap: spacing.sm,
  },
  badge: {
    alignSelf: "flex-start",
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: radius.pill,
    backgroundColor: "#FEE2D1",
  },
  badgeText: {
    color: colors.brandDeep,
    fontWeight: "700",
  },
});
