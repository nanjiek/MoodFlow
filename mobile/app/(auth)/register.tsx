import { useState } from "react";
import { router } from "expo-router";

import { BrandHero } from "@/components/app/brand-hero";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Screen } from "@/components/ui/screen";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/types/api";
import { fieldErrorText } from "@/lib/format";

export default function RegisterScreen() {
  const { signUp } = useAuth();
  const toast = useToast();
  const [nickname, setNickname] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    setErrors({});
    try {
      await signUp(phone, password, nickname);
      router.replace("/(app)/(tabs)");
    } catch (rawError) {
      const apiError = rawError as ApiError;
      setErrors({
        nickname: fieldErrorText(apiError.fieldErrors?.nickname),
        phone: fieldErrorText(apiError.fieldErrors?.phone),
        password: fieldErrorText(apiError.fieldErrors?.password),
      });
      toast.show(apiError.message, "danger");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <BrandHero title="打开你的情绪空间。" description="注册成功后会直接进入首页，开始第一条记录。" />
      <Input label="昵称" value={nickname} onChangeText={setNickname} error={errors.nickname} />
      <Input label="手机号" value={phone} onChangeText={setPhone} keyboardType="phone-pad" error={errors.phone} />
      <Input label="密码" value={password} onChangeText={setPassword} secureTextEntry error={errors.password} />
      <Button title="注册并进入首页" onPress={handleSubmit} loading={loading} />
      <Button title="已有账号，去登录" tone="ghost" onPress={() => router.back()} />
    </Screen>
  );
}
