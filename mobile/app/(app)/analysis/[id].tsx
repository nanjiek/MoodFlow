import { router, useLocalSearchParams } from "expo-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Input } from "@/components/ui/input";
import { InlineAlert } from "@/components/ui/inline-alert";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading, Subheading } from "@/components/ui/text";
import { EMOTION_OPTIONS } from "@/constants/emotions";
import { fetchAnalysis, submitAnalysisCorrection } from "@/lib/api/emotions";

export default function AnalysisDetailScreen() {
  const params = useLocalSearchParams<{ id: string }>();
  const recordId = Number(params.id);
  const analysisQuery = useQuery({
    queryKey: ["analysis", recordId],
    queryFn: () => fetchAnalysis(recordId),
  });
  const [accepted, setAccepted] = useState(false);
  const [correctedLabel, setCorrectedLabel] = useState("calm");
  const [note, setNote] = useState("");
  const [notice, setNotice] = useState<{ message: string; tone: "success" | "danger" } | null>(null);
  const correctionMutation = useMutation({
    mutationFn: () => submitAnalysisCorrection(recordId, { accepted, corrected_label: correctedLabel, note }),
    onMutate: () => {
      setNotice(null);
    },
    onSuccess: () => {
      setNotice({ message: "纠正结果已提交，感谢你的反馈。", tone: "success" });
    },
    onError: () => {
      setNotice({ message: "提交失败，请稍后再试。", tone: "danger" });
    },
  });

  const analysis = analysisQuery.data;

  return (
    <Screen>
      <Heading>分析结果</Heading>
      <BodyText>这里会展示当前情绪判断、关键词和陪伴建议；看完后你也可以直接返回继续记录。</BodyText>
      <Card>
        <Subheading>{analysis?.predicted_label_detail.display_name ?? "分析中"}</Subheading>
        <BodyText>{analysis?.explanation ?? "正在等待模型返回更完整的说明。"}</BodyText>
        <BodyText>关键词：{analysis?.keywords.join(" / ") || "暂无"}</BodyText>
        <BodyText>温和反馈：{analysis?.gentle_feedback ?? "稍后生成"}</BodyText>
      </Card>
      {(analysis?.companion_suggestions ?? []).map((item) => (
        <Card key={item.id}>
          <Subheading>{item.title}</Subheading>
          <BodyText>{item.body}</BodyText>
        </Card>
      ))}
      <Card>
        <Subheading>纠正分析</Subheading>
        <BodyText>如果这次判断不贴近你的感受，可以直接提交纠正。</BodyText>
        {notice ? <InlineAlert message={notice.message} tone={notice.tone} /> : null}
        <Button title={accepted ? "我认可这次分析" : "我不太认同这次分析"} tone="soft" onPress={() => setAccepted((value) => !value)} />
        <BodyText>如果不认同，可以选一个更贴近的情绪：</BodyText>
        {EMOTION_OPTIONS.map((item) => (
          <Chip key={item.code} label={item.label} selected={correctedLabel === item.code} onPress={() => setCorrectedLabel(item.code)} />
        ))}
        <Input label="补充说明" multiline value={note} onChangeText={setNote} />
        <Button title="提交纠正" onPress={() => correctionMutation.mutate()} loading={correctionMutation.isPending} />
        <Button title="查看记录列表" tone="ghost" onPress={() => router.replace("/(app)/(tabs)/records")} />
        <Button title="完成并返回首页" tone="soft" onPress={() => router.replace("/(app)/(tabs)")} />
      </Card>
    </Screen>
  );
}
