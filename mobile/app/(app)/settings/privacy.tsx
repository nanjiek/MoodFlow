import { useQuery, useMutation } from "@tanstack/react-query";
import { Switch } from "react-native";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { InlineAlert } from "@/components/ui/inline-alert";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading } from "@/components/ui/text";
import { fetchPrivacy, updatePrivacy } from "@/lib/api/auth";

export default function PrivacySettingsScreen() {
  const privacyQuery = useQuery({
    queryKey: ["privacy"],
    queryFn: fetchPrivacy,
  });
  const mutation = useMutation({
    mutationFn: () =>
      updatePrivacy({
        anonymous_mode: !(privacyQuery.data?.anonymous_mode ?? false),
        emotion_encryption_enabled: privacyQuery.data?.emotion_encryption_enabled ?? false,
      }),
  });
  const encryptionMutation = useMutation({
    mutationFn: () =>
      updatePrivacy({
        anonymous_mode: privacyQuery.data?.anonymous_mode ?? false,
        emotion_encryption_enabled: !(privacyQuery.data?.emotion_encryption_enabled ?? false),
      }),
  });

  return (
    <Screen>
      <Heading>隐私设置</Heading>
      <InlineAlert message="首版不做假的“绝对安全”承诺，只展示真实的匿名与加密开关状态。" />
      <Card style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
        <BodyText>匿名模式</BodyText>
        <Switch value={privacyQuery.data?.anonymous_mode ?? false} onValueChange={() => mutation.mutate()} />
      </Card>
      <Card style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
        <BodyText>情绪记录加密</BodyText>
        <Switch
          value={privacyQuery.data?.emotion_encryption_enabled ?? false}
          onValueChange={() => encryptionMutation.mutate()}
        />
      </Card>
      <Button title="刷新当前状态" tone="ghost" onPress={() => privacyQuery.refetch()} />
    </Screen>
  );
}
