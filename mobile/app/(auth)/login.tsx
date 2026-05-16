import { useState } from "react";
import { Link, router } from "expo-router";
import { Pressable, StyleSheet, View } from "react-native";

import { BrandHero } from "@/components/app/brand-hero";
import { Button } from "@/components/ui/button";
import { InlineAlert } from "@/components/ui/inline-alert";
import { Input } from "@/components/ui/input";
import { Screen } from "@/components/ui/screen";
import { BodyText, CaptionText } from "@/components/ui/text";
import { colors, spacing } from "@/constants/theme";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/types/api";

export default function LoginScreen() {
  const { signIn } = useAuth();
  const toast = useToast();
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    try {
      await signIn(phone, password);
      router.replace("/(app)/(tabs)");
    } catch (rawError) {
      const apiError = rawError as ApiError;
      setError(apiError.message);
      toast.show("登录失败，请检查手机号和密码。", "danger");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <BrandHero />
      {error ? <InlineAlert message={error} tone="danger" /> : null}
      <Input label="手机号" value={phone} onChangeText={setPhone} keyboardType="phone-pad" />
      <Input label="密码" value={password} onChangeText={setPassword} secureTextEntry />
      <Button title="登录 MoodFlow" onPress={handleSubmit} loading={loading} />
      <View style={styles.links}>
        <Link href="/(auth)/register" asChild>
          <Pressable>
            <CaptionText style={styles.linkText}>去注册</CaptionText>
          </Pressable>
        </Link>
        <Link href="/(auth)/forgot/send-code" asChild>
          <Pressable>
            <CaptionText style={styles.linkText}>找回密码</CaptionText>
          </Pressable>
        </Link>
      </View>
      <Pressable style={styles.socialEntry} onPress={() => router.push("/(auth)/social")}>
        <BodyText style={{ color: colors.brandDeep }}>微信 / QQ 登录入口预留</BodyText>
      </Pressable>
    </Screen>
  );
}

const styles = StyleSheet.create({
  links: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  linkText: {
    color: colors.brandDeep,
    fontWeight: "700",
  },
  socialEntry: {
    borderWidth: 1,
    borderColor: colors.line,
    borderStyle: "dashed",
    borderRadius: 22,
    padding: spacing.md,
    alignItems: "center",
  },
});
