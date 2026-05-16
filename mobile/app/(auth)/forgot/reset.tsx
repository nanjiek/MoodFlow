import { useLocalSearchParams, router } from "expo-router";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading } from "@/components/ui/text";
import { resetPassword } from "@/lib/api/auth";
import { useToast } from "@/hooks/useToast";

export default function ForgotResetScreen() {
  const params = useLocalSearchParams<{ phone?: string; requestId?: string; code?: string }>();
  const toast = useToast();
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleReset = async () => {
    setLoading(true);
    try {
      await resetPassword(params.phone ?? "", params.requestId ?? "", params.code ?? "", password);
      toast.show("密码已重置，请重新登录。", "success");
      router.replace("/(auth)/login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <Heading>设置新密码</Heading>
      <BodyText>如果请求已过期或无效，后端会返回统一错误提示，不暴露账号状态。</BodyText>
      <Input label="新密码" value={password} onChangeText={setPassword} secureTextEntry />
      <Button title="提交新密码" onPress={handleReset} loading={loading} />
    </Screen>
  );
}
