import { useEffect, useState } from "react";
import { useLocalSearchParams, router } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Switch } from "react-native";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading } from "@/components/ui/text";
import { fetchRecords, updateRecord } from "@/lib/api/emotions";

export default function RecordDetailScreen() {
  const params = useLocalSearchParams<{ id: string }>();
  const recordId = Number(params.id);
  const queryClient = useQueryClient();
  const recordQuery = useQuery({
    queryKey: ["records", "detail", recordId],
    queryFn: async () => {
      const page = await fetchRecords();
      return page.results.find((item) => item.id === recordId) ?? null;
    },
  });

  const record = recordQuery.data;
  const [text, setText] = useState("");
  const [isEncrypted, setIsEncrypted] = useState(false);

  useEffect(() => {
    if (!record) {
      return;
    }
    setText(record.text ?? "");
    setIsEncrypted(record.is_encrypted);
  }, [record]);

  const updateMutation = useMutation({
    mutationFn: async () => {
      if (!record) {
        return null;
      }
      return updateRecord(record.id, {
        selected_label: record.selected_label,
        text,
        is_encrypted: isEncrypted,
        is_collect: record.is_collect,
        emoji_id: record.emoji_id,
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["records"] });
      router.back();
    },
  });

  if (!record) {
    return (
      <Screen>
        <Heading>记录暂不可用</Heading>
        <BodyText>这条记录可能已被删除，或暂时还没有加载完成。</BodyText>
      </Screen>
    );
  }

  return (
    <Screen>
      <Heading>编辑记录</Heading>
      <BodyText>你可以更新这条记录的文字内容，也可以调整是否加密保存。</BodyText>
      <Input label="记录内容" multiline value={text} onChangeText={setText} />
      <Card style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
        <BodyText>保持加密</BodyText>
        <Switch value={isEncrypted} onValueChange={setIsEncrypted} />
      </Card>
      <Button title="保存修改" onPress={() => updateMutation.mutate()} loading={updateMutation.isPending} />
      <Button title="查看分析结果" tone="soft" onPress={() => router.push(`/(app)/analysis/${record.id}`)} />
    </Screen>
  );
}
