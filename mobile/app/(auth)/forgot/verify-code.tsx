import { useLocalSearchParams, router } from "expo-router";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { InlineAlert } from "@/components/ui/inline-alert";
import { Input } from "@/components/ui/input";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading } from "@/components/ui/text";
import { verifyPasswordResetCode } from "@/lib/api/auth";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/types/api";

export default function ForgotVerifyCodeScreen() {
  const params = useLocalSearchParams<{ phone?: string; requestId?: string; debugCode?: string }>();
  const toast = useToast();
  const [code, setCode] = useState(params.debugCode ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleVerify = async () => {
    setLoading(true);
    setError("");
    try {
      await verifyPasswordResetCode(params.phone ?? "", params.requestId ?? "", code);
      router.push({
        pathname: "/(auth)/forgot/reset",
        params: { phone: params.phone, requestId: params.requestId, code },
      });
    } catch (rawError) {
      const apiError = rawError as ApiError;
      setError(apiError.message);
      toast.show("验证码校验失败，请重试。", "danger");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <Heading>校验验证码</Heading>
      <BodyText>输入收到的验证码后，才能进入重置密码步骤。</BodyText>
      {params.debugCode ? <InlineAlert message={`当前环境提供了验证码参考：${params.debugCode}`} tone="warning" /> : null}
      {error ? <InlineAlert message={error} tone="danger" /> : null}
      <Input label="验证码" value={code} onChangeText={setCode} keyboardType="number-pad" />
      <Button title="继续重置密码" onPress={handleVerify} loading={loading} />
    </Screen>
  );
}
