import { StyleSheet, View } from "react-native";

import { Card } from "@/components/ui/card";
import { BodyText, CaptionText, Heading } from "@/components/ui/text";
import { colors, radius, spacing } from "@/constants/theme";

export function BrandHero({
  eyebrow = "MoodFlow 移动端展示版",
  title = "把情绪记录、分析和成长回看放进一只手里。",
  description = "真实接口优先，可演示、可联调、主要流程可跑通。",
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
