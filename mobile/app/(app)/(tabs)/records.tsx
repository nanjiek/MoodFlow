import { useMemo, useState } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { router } from "expo-router";
import { View } from "react-native";

import { RecordCard } from "@/components/app/record-card";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { EmptyState } from "@/components/ui/empty-state";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading } from "@/components/ui/text";
import { EMOTION_OPTIONS } from "@/constants/emotions";
import { fetchRecords, toggleFavorite } from "@/lib/api/emotions";

export default function RecordsTabScreen() {
  const queryClient = useQueryClient();
  const [selectedLabel, setSelectedLabel] = useState<string | undefined>();
  const recordsQuery = useQuery({
    queryKey: ["records", selectedLabel],
    queryFn: () => fetchRecords({ selectedLabel }),
  });
  const toggleMutation = useMutation({
    mutationFn: ({ id, current }: { id: number; current: boolean }) => toggleFavorite(id, !current),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["records"] }),
  });

  const records = useMemo(() => recordsQuery.data?.results ?? [], [recordsQuery.data]);

  return (
    <Screen>
      <Heading>记录</Heading>
      <BodyText>在这里查看你的情绪记录，也可以按情绪筛选、收藏和回看分析。</BodyText>
      <Button title="新建记录" onPress={() => router.push("/(app)/record/new")} />
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
        <Chip label="全部" selected={!selectedLabel} onPress={() => setSelectedLabel(undefined)} />
        {EMOTION_OPTIONS.map((item) => (
          <Chip
            key={item.code}
            label={item.label}
            selected={selectedLabel === item.code}
            onPress={() => setSelectedLabel(item.code)}
          />
        ))}
      </View>
      {records.length ? (
        records.map((record) => (
          <RecordCard
            key={record.id}
            record={record}
            onPress={() => router.push(`/(app)/record/${record.id}`)}
            onToggleFavorite={() => toggleMutation.mutate({ id: record.id, current: record.is_collect })}
          />
        ))
      ) : (
        <EmptyState title="还没有符合条件的记录" description="先记录一次心情，后面才能看到筛选、分析和成长轨迹。" />
      )}
    </Screen>
  );
}
