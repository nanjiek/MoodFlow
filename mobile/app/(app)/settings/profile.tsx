import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading } from "@/components/ui/text";
import { useAuth } from "@/hooks/useAuth";
import { updateProfile } from "@/lib/api/auth";

export default function ProfileSettingsScreen() {
  const { profile, updateCachedProfile } = useAuth();
  const [nickname, setNickname] = useState(profile?.nickname ?? "");
  const [email, setEmail] = useState(profile?.email ?? "");
  const [signature, setSignature] = useState(profile?.signature ?? "");

  useEffect(() => {
    setNickname(profile?.nickname ?? "");
    setEmail(profile?.email ?? "");
    setSignature(profile?.signature ?? "");
  }, [profile]);

  const mutation = useMutation({
    mutationFn: () => updateProfile({ nickname, email, signature }),
    onSuccess: async (nextProfile) => {
      await updateCachedProfile(nextProfile);
    },
  });

  return (
    <Screen>
      <Heading>个人资料</Heading>
      <BodyText>昵称、邮箱与签名均接真实资料更新接口。</BodyText>
      <Input label="昵称" value={nickname} onChangeText={setNickname} />
      <Input label="邮箱" value={email} onChangeText={setEmail} keyboardType="email-address" />
      <Input label="签名" value={signature} onChangeText={setSignature} multiline />
      <Button title="保存资料" onPress={() => mutation.mutate()} loading={mutation.isPending} />
    </Screen>
  );
}
