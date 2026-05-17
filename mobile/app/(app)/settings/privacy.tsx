import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Switch } from "react-native";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { InlineAlert } from "@/components/ui/inline-alert";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading } from "@/components/ui/text";
import { fetchPrivacy, updatePrivacy } from "@/lib/api/auth";

export default function PrivacySettingsScreen() {
  const queryClient = useQueryClient();
  const privacyQuery = useQuery({
    queryKey: ["privacy"],
    queryFn: fetchPrivacy,
  });
  const [anonymousMode, setAnonymousMode] = useState(false);
  const [encryptionEnabled, setEncryptionEnabled] = useState(false);
  const [notice, setNotice] = useState<{ message: string; tone: "danger" } | null>(null);
  const [pendingTarget, setPendingTarget] = useState<"anonymous" | "encryption" | null>(null);

  useEffect(() => {
    if (!privacyQuery.data) {
      return;
    }
    setAnonymousMode(privacyQuery.data.anonymous_mode);
    setEncryptionEnabled(privacyQuery.data.emotion_encryption_enabled);
  }, [privacyQuery.data]);

  const mutation = useMutation({
    mutationFn: updatePrivacy,
    onMutate: async (nextState) => {
      setNotice(null);
      await queryClient.cancelQueries({ queryKey: ["privacy"] });
      const previous = queryClient.getQueryData<Awaited<ReturnType<typeof fetchPrivacy>>>(["privacy"]);
      queryClient.setQueryData(["privacy"], nextState);
      return { previous };
    },
    onSuccess: (nextState) => {
      setAnonymousMode(nextState.anonymous_mode);
      setEncryptionEnabled(nextState.emotion_encryption_enabled);
    },
    onError: (_error, _variables, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["privacy"], context.previous);
        setAnonymousMode(context.previous.anonymous_mode);
        setEncryptionEnabled(context.previous.emotion_encryption_enabled);
      }
      setNotice({ message: "更新失败，请稍后重试。", tone: "danger" });
    },
    onSettled: () => {
      setPendingTarget(null);
      queryClient.invalidateQueries({ queryKey: ["privacy"] });
    },
  });

  const handleUpdate = (
    target: "anonymous" | "encryption",
    nextState: { anonymous_mode: boolean; emotion_encryption_enabled: boolean },
  ) => {
    setPendingTarget(target);
    setAnonymousMode(nextState.anonymous_mode);
    setEncryptionEnabled(nextState.emotion_encryption_enabled);
    mutation.mutate(nextState);
  };

  return (
    <Screen>
      <Heading>隐私设置</Heading>
      <InlineAlert message="你可以按需要开启匿名模式或加密记录，后续随时都能回来调整。" />
      {notice ? <InlineAlert message={notice.message} tone={notice.tone} /> : null}
      <Card style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
        <BodyText>匿名模式</BodyText>
        <Switch
          disabled={pendingTarget === "anonymous"}
          value={anonymousMode}
          onValueChange={(value) =>
            handleUpdate("anonymous", {
              anonymous_mode: value,
              emotion_encryption_enabled: encryptionEnabled,
            })
          }
        />
      </Card>
      <Card style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
        <BodyText>情绪记录加密</BodyText>
        <Switch
          disabled={pendingTarget === "encryption"}
          value={encryptionEnabled}
          onValueChange={(value) =>
            handleUpdate("encryption", {
              anonymous_mode: anonymousMode,
              emotion_encryption_enabled: value,
            })
          }
        />
      </Card>
      <Button title="刷新当前状态" tone="ghost" onPress={() => privacyQuery.refetch()} />
    </Screen>
  );
}
