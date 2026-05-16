import { useState } from "react";
import { router } from "expo-router";

import { Button } from "@/components/ui/button";
import { InlineAlert } from "@/components/ui/inline-alert";
import { Input } from "@/components/ui/input";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading } from "@/components/ui/text";
import { sendPasswordResetCode } from "@/lib/api/auth";
import { useToast } from "@/hooks/useToast";

export default function ForgotSendCodeScreen() {
  const toast = useToast();
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [hint, setHint] = useState("");

  const handleSend = async () => {
    setLoading(true);
    try {
      const result = await sendPasswordResetCode(phone);
      setHint("验证码已发送。如果该手机号已注册，请继续输入验证码完成下一步。");
      toast.show("验证码请求已提交。", "success");
      router.push({
        pathname: "/(auth)/forgot/verify-code",
        params: { phone, requestId: result.request_id, debugCode: result.debug_code ?? "" },
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <Heading>找回密码</Heading>
      <BodyText>第一步会统一提示发码结果，不会暴露手机号是否已注册。</BodyText>
      {hint ? <InlineAlert message={hint} /> : null}
      <Input label="手机号" value={phone} onChangeText={setPhone} keyboardType="phone-pad" />
      <Button title="发送验证码" onPress={handleSend} loading={loading} />
    </Screen>
  );
}
