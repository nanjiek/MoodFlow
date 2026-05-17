import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { LayoutChangeEvent, StyleSheet, View } from "react-native";

import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading, Subheading } from "@/components/ui/text";
import { colors, spacing } from "@/constants/theme";
import { fetchDailyReport, fetchGrowthCurve, fetchWeeklyReport } from "@/lib/api/emotions";

function GrowthLineChart({
  series,
}: {
  series: Array<{ date: string; score: number; record_count: number }>;
}) {
  const [width, setWidth] = useState(0);
  const chartHeight = 132;
  const labelWidth = 52;
  const horizontalPadding = 18;
  const rawMinScore = Math.min(...series.map((point) => point.score));
  const rawMaxScore = Math.max(...series.map((point) => point.score));
  const rawRange = rawMaxScore - rawMinScore;
  const scorePadding = rawRange === 0 ? 2 : Math.max(rawRange * 0.25, 0.8);
  const minScore = Math.max(0, rawMinScore - scorePadding);
  const maxScore = rawMaxScore + scorePadding;
  const scoreRange = Math.max(maxScore - minScore, 1);

  const handleLayout = (event: LayoutChangeEvent) => {
    setWidth(event.nativeEvent.layout.width);
  };

  const usableWidth = Math.max(width - horizontalPadding * 2, 0);
  const stepX = series.length > 1 ? usableWidth / (series.length - 1) : 0;
  const points = series.map((point, index) => {
    const x = horizontalPadding + stepX * index;
    const normalized = (point.score - minScore) / scoreRange;
    const y = chartHeight - normalized * (chartHeight - 16) - 8;
    return { ...point, x, y };
  });

  return (
    <View onLayout={handleLayout} style={styles.chartShell}>
      <View style={[styles.chartArea, { height: chartHeight }]}>
        {[0, 0.5, 1].map((ratio) => (
          <View
            key={ratio}
            style={[
              styles.gridLine,
              {
                top: 8 + (chartHeight - 16) * ratio,
              },
            ]}
          />
        ))}
        {points.map((point, index) => {
          const next = points[index + 1];
          if (!next) {
            return null;
          }
          const dx = next.x - point.x;
          const dy = next.y - point.y;
          const length = Math.sqrt(dx * dx + dy * dy);
          const angle = `${(Math.atan2(dy, dx) * 180) / Math.PI}deg`;
          return (
            <View
              key={`${point.date}-${next.date}`}
              style={[
                styles.segment,
                {
                  left: point.x,
                  top: point.y,
                  width: length,
                  transform: [{ rotate: angle }],
                },
              ]}
            />
          );
        })}
        {points.map((point) => (
          <View key={point.date} style={[styles.pointWrap, { left: point.x - labelWidth / 2, top: point.y - 10, width: labelWidth }]}>
            <View style={styles.pointDot} />
            <BodyText style={styles.pointLabel}>{point.score.toFixed(1)}</BodyText>
          </View>
        ))}
      </View>
      <View style={styles.labelRow}>
        {points.map((point) => (
          <View key={`${point.date}-label`} style={[styles.axisLabelWrap, { left: point.x - labelWidth / 2, width: labelWidth }]}>
            <BodyText style={styles.axisLabel}>{point.date.slice(5)}</BodyText>
          </View>
        ))}
      </View>
    </View>
  );
}

export default function GrowthTabScreen() {
  const [mode, setMode] = useState<"daily" | "weekly">("daily");
  const growthQuery = useQuery({
    queryKey: ["growth", 7],
    queryFn: () => fetchGrowthCurve(7, new Date().toISOString().slice(0, 10)),
  });
  const dailyQuery = useQuery({
    queryKey: ["report", "daily"],
    queryFn: () => fetchDailyReport(),
  });
  const weeklyQuery = useQuery({
    queryKey: ["report", "weekly"],
    queryFn: () => fetchWeeklyReport(),
  });

  const report = mode === "daily" ? dailyQuery.data : weeklyQuery.data;

  return (
    <Screen>
      <Heading>成长</Heading>
      <BodyText>这里会汇总最近的记录变化，帮你更轻松地回看自己的情绪节奏。</BodyText>
      <Card>
        <Subheading>成长曲线</Subheading>
        <BodyText>最近 {growthQuery.data?.days ?? 7} 天平均分：{growthQuery.data?.summary.average_score ?? "--"}</BodyText>
        {(growthQuery.data?.series ?? []).length > 0 ? (
          <>
            <GrowthLineChart series={growthQuery.data?.series ?? []} />
            {(growthQuery.data?.series ?? []).map((point) => (
              <View key={point.date} style={{ flexDirection: "row", justifyContent: "space-between" }}>
                <BodyText>{point.date}</BodyText>
                <BodyText>
                  {point.score} 分 | {point.record_count} 条记录
                </BodyText>
              </View>
            ))}
          </>
        ) : (
          <BodyText>再多记录几天，这里就会形成一条更清晰的情绪变化曲线。</BodyText>
        )}
      </Card>
      <View style={{ flexDirection: "row", gap: 8 }}>
        <Chip label="日报" selected={mode === "daily"} onPress={() => setMode("daily")} />
        <Chip label="周报" selected={mode === "weekly"} onPress={() => setMode("weekly")} />
      </View>
      <Card>
        <Subheading>{mode === "daily" ? "今日摘要" : "本周摘要"}</Subheading>
        <BodyText>{report?.summary.summary ?? "记录还不够多，继续写下最近的感受后，这里会慢慢丰富起来。"}</BodyText>
        {(report?.summary.highlights ?? []).map((highlight) => (
          <BodyText key={highlight}>* {highlight}</BodyText>
        ))}
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  chartShell: {
    marginTop: spacing.sm,
    marginBottom: spacing.md,
  },
  chartArea: {
    position: "relative",
    borderRadius: 16,
    backgroundColor: colors.surfaceMuted,
    overflow: "hidden",
  },
  gridLine: {
    position: "absolute",
    left: 12,
    right: 12,
    height: 1,
    backgroundColor: colors.line,
  },
  segment: {
    position: "absolute",
    height: 3,
    backgroundColor: colors.brand,
    borderRadius: 999,
    transformOrigin: "left center",
  },
  pointWrap: {
    position: "absolute",
    alignItems: "center",
  },
  pointDot: {
    width: 10,
    height: 10,
    borderRadius: 999,
    backgroundColor: colors.brandDeep,
    borderWidth: 2,
    borderColor: colors.surface,
  },
  pointLabel: {
    marginTop: 4,
    fontSize: 12,
    color: colors.inkMuted,
  },
  labelRow: {
    position: "relative",
    height: 24,
    marginTop: spacing.xs,
  },
  axisLabelWrap: {
    position: "absolute",
    alignItems: "center",
  },
  axisLabel: {
    fontSize: 12,
    color: colors.inkSoft,
  },
});
