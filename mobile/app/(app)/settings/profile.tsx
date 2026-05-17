import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { InlineAlert } from "@/components/ui/inline-alert";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading } from "@/components/ui/text";
import { useAuth } from "@/hooks/useAuth";
import { updateProfile } from "@/lib/api/auth";

export default function ProfileSettingsScreen() {
  const { profile, updateCachedProfile } = useAuth();
  const [nickname, setNickname] = useState(profile?.nickname ?? "");
  const [email, setEmail] = useState(profile?.email ?? "");
  const [signature, setSignature] = useState(profile?.signature ?? "");
  const [notice, setNotice] = useState<{ message: string; tone: "success" | "danger" } | null>(null);

  useEffect(() => {
    setNickname(profile?.nickname ?? "");
    setEmail(profile?.email ?? "");
    setSignature(profile?.signature ?? "");
  }, [profile]);

  const mutation = useMutation({
    mutationFn: () => updateProfile({ nickname, email, signature }),
    onMutate: () => {
      setNotice(null);
    },
    onSuccess: async (nextProfile) => {
      await updateCachedProfile(nextProfile);
      setNotice({ message: "资料已保存。", tone: "success" });
    },
    onError: () => {
      setNotice({ message: "保存失败，请稍后重试。", tone: "danger" });
    },
  });

  return (
    <Screen>
      <Heading>个人资料</Heading>
      <BodyText>完善你的昵称、邮箱和签名，让这里更像你的私人角落。</BodyText>
      {notice ? <InlineAlert message={notice.message} tone={notice.tone} /> : null}
      <Input label="昵称" value={nickname} onChangeText={setNickname} />
      <Input label="邮箱" value={email} onChangeText={setEmail} keyboardType="email-address" />
      <Input label="签名" value={signature} onChangeText={setSignature} multiline />
      <Button title="保存资料" onPress={() => mutation.mutate()} loading={mutation.isPending} />
    </Screen>
  );
}
