import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { router } from "expo-router";
import { Pressable, StyleSheet, Switch, Text, View } from "react-native";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading } from "@/components/ui/text";
import { EMOTION_OPTIONS } from "@/constants/emotions";
import { spacing } from "@/constants/theme";
import { createRecord } from "@/lib/api/emotions";
import { getRecordDraft, setRecordDraft } from "@/lib/storage";

export default function RecordCreateScreen() {
  const queryClient = useQueryClient();
  const [selectedLabel, setSelectedLabel] = useState("plain");
  const [text, setText] = useState("");
  const [emojiId, setEmojiId] = useState("");
  const [isEncrypted, setIsEncrypted] = useState(false);

  useEffect(() => {
    void getRecordDraft().then((draft) => {
      if (draft) {
        setText(draft);
      }
    });
  }, []);

  useEffect(() => {
    void setRecordDraft(text);
  }, [text]);

  const createMutation = useMutation({
    mutationFn: () =>
      createRecord({
        selected_label: selectedLabel,
        text,
        emoji_id: emojiId,
        is_encrypted: isEncrypted,
        recorded_at: new Date().toISOString(),
      }),
    onSuccess: async (record) => {
      await queryClient.invalidateQueries({ queryKey: ["records"] });
      await queryClient.invalidateQueries({ queryKey: ["daily-report"] });
      await setRecordDraft(null);
      router.replace(`/(app)/analysis/${record.id}`);
    },
  });

  return (
    <Screen>
      <Heading>记录此刻情绪</Heading>
      <BodyText>首版按 P0 方向做成 30 秒内可完成的一次轻量记录。</BodyText>
      <Card>
        <View style={styles.grid}>
          {EMOTION_OPTIONS.map((item) => (
            <Pressable
              key={item.code}
              style={[styles.emotionCard, selectedLabel === item.code ? { backgroundColor: item.tint } : null]}
              onPress={() => setSelectedLabel(item.code)}
            >
              <Text style={styles.emotionEmoji}>{item.emoji}</Text>
              <Text>{item.label}</Text>
              <Text>{item.description}</Text>
            </Pressable>
          ))}
        </View>
      </Card>
      <Input label="一句话记录" multiline value={text} onChangeText={setText} placeholder="今天让你最有感觉的一刻是什么？" />
      <Input label="可选 emoji id" value={emojiId} onChangeText={setEmojiId} placeholder="例如 smile-1" />
      <Card style={styles.toggleRow}>
        <BodyText>开启加密记录</BodyText>
        <Switch value={isEncrypted} onValueChange={setIsEncrypted} />
      </Card>
      <Button title="保存并生成分析" onPress={() => createMutation.mutate()} loading={createMutation.isPending} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  emotionCard: {
    width: "47%",
    minHeight: 100,
    borderRadius: 18,
    padding: spacing.sm,
    backgroundColor: "#F7F3EF",
    gap: 4,
  },
  emotionEmoji: {
    fontSize: 24,
  },
  toggleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
});
