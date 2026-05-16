import { Pressable, StyleSheet, Text, View } from "react-native";

import { Card } from "@/components/ui/card";
import { BodyText, CaptionText, Subheading } from "@/components/ui/text";
import { EMOTION_BY_CODE } from "@/constants/emotions";
import { colors, spacing } from "@/constants/theme";
import { formatDateTime } from "@/lib/format";
import type { EmotionRecord } from "@/types/domain";

export function RecordCard({
  record,
  onPress,
  onToggleFavorite,
}: {
  record: EmotionRecord;
  onPress?: () => void;
  onToggleFavorite?: () => void;
}) {
  const emotion = EMOTION_BY_CODE[record.selected_label];
  return (
    <Pressable onPress={onPress}>
      <Card>
        <View style={styles.row}>
          <View style={styles.rowGap}>
            <Text style={styles.emoji}>{record.emoji_id ? "✨" : emotion.emoji}</Text>
            <View>
              <Subheading>{emotion.label}</Subheading>
              <CaptionText>{formatDateTime(record.recorded_at)}</CaptionText>
            </View>
          </View>
          <Pressable onPress={onToggleFavorite}>
            <Text style={styles.favorite}>{record.is_collect ? "★" : "☆"}</Text>
          </Pressable>
        </View>
        <BodyText>{record.text || "这条记录只保留了情绪和瞬间，没有额外文字。"}</BodyText>
        <View style={styles.footer}>
          <CaptionText>{record.is_encrypted ? "已加密" : "普通记录"}</CaptionText>
          <CaptionText>{record.analysis?.predicted_label_detail?.display_name ?? "分析处理中"}</CaptionText>
        </View>
      </Card>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  rowGap: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  emoji: {
    fontSize: 24,
  },
  favorite: {
    fontSize: 22,
    color: colors.brandDeep,
  },
  footer: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
});
