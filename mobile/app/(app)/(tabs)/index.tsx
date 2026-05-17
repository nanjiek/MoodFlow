import { useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { Pressable, StyleSheet, View } from "react-native";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Screen } from "@/components/ui/screen";
import { BodyText, CaptionText, Heading, Subheading } from "@/components/ui/text";
import { fetchCompanionRecommendations, fetchDailyReport } from "@/lib/api/emotions";
import { colors, spacing } from "@/constants/theme";
import { formatDate } from "@/lib/format";

export default function HomeTabScreen() {
  const dailyQuery = useQuery({
    queryKey: ["daily-report"],
    queryFn: () => fetchDailyReport(),
  });
  const companionQuery = useQuery({
    queryKey: ["companion"],
    queryFn: () => fetchCompanionRecommendations(3),
  });

  const latestSummary = dailyQuery.data?.summary.summary ?? "今天还没有记录，先从一次轻量记录开始。";
  const dominant = dailyQuery.data?.dominant_emotion?.display_name ?? "等待第一条情绪信号";

  return (
    <Screen>
      <Heading>今天想先记下哪一刻？</Heading>
      <BodyText>先用一句话记下此刻的感受，后面再慢慢补充也可以。</BodyText>
      <Button title="记录此刻情绪" onPress={() => router.push("/(app)/record/new")} />
      <Card>
        <CaptionText>最近一次情绪摘要</CaptionText>
        <Subheading>{dominant}</Subheading>
        <BodyText>{latestSummary}</BodyText>
        <CaptionText>{formatDate(new Date().toISOString())}</CaptionText>
      </Card>
      <Card>
        <CaptionText>提醒状态摘要</CaptionText>
        <Subheading>{dailyQuery.data ? "提醒设置已同步" : "提醒功能可用"}</Subheading>
        <BodyText>你可以调整提醒时间、频率和偏好内容，让记录节奏更贴合自己的日常。</BodyText>
        <Button title="前往提醒设置" tone="soft" onPress={() => router.push("/(app)/settings/reminders")} />
      </Card>
      <View style={styles.sectionHeader}>
        <Subheading>陪伴内容推荐</Subheading>
        <Pressable onPress={() => companionQuery.refetch()}>
          <CaptionText style={{ color: colors.brandDeep }}>刷新</CaptionText>
        </Pressable>
      </View>
      {(companionQuery.data?.recommendations ?? []).map((item) => (
        <Card key={item.id}>
          <CaptionText>{item.content_type}</CaptionText>
          <Subheading>{item.title}</Subheading>
          <BodyText>{item.body}</BodyText>
        </Card>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: spacing.sm,
  },
});
