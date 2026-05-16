import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { View } from "react-native";

import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading, Subheading } from "@/components/ui/text";
import { fetchDailyReport, fetchGrowthCurve, fetchWeeklyReport } from "@/lib/api/emotions";

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
      <Heading>Growth</Heading>
      <BodyText>The growth curve, daily report, and weekly summary all come from real backend analytics.</BodyText>
      <Card>
        <Subheading>Growth Curve</Subheading>
        <BodyText>Average score for the last {growthQuery.data?.days ?? 7} days: {growthQuery.data?.summary.average_score ?? "--"}</BodyText>
        {(growthQuery.data?.series ?? []).map((point) => (
          <View key={point.date} style={{ flexDirection: "row", justifyContent: "space-between" }}>
            <BodyText>{point.date}</BodyText>
            <BodyText>
              {point.score} pts | {point.record_count} records
            </BodyText>
          </View>
        ))}
      </Card>
      <View style={{ flexDirection: "row", gap: 8 }}>
        <Chip label="Daily" selected={mode === "daily"} onPress={() => setMode("daily")} />
        <Chip label="Weekly" selected={mode === "weekly"} onPress={() => setMode("weekly")} />
      </View>
      <Card>
        <Subheading>{mode === "daily" ? "Daily Summary" : "Weekly Summary"}</Subheading>
        <BodyText>{report?.summary.summary ?? "There are not enough records yet to build a summary."}</BodyText>
        {(report?.summary.highlights ?? []).map((highlight) => (
          <BodyText key={highlight}>* {highlight}</BodyText>
        ))}
      </Card>
    </Screen>
  );
}
