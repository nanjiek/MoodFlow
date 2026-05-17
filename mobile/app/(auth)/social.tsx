import { router } from "expo-router";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading, Subheading } from "@/components/ui/text";
import { SOCIAL_PLACEHOLDER_COPY } from "@/constants/content";

export default function SocialLoginPlaceholderScreen() {
  return (
    <Screen>
      <Heading>{SOCIAL_PLACEHOLDER_COPY.title}</Heading>
      <BodyText>{SOCIAL_PLACEHOLDER_COPY.description}</BodyText>
      <Card>
        <Subheading>微信登录</Subheading>
        <BodyText>入口已预留，后续接入正式授权后即可使用。</BodyText>
      </Card>
      <Card>
        <Subheading>QQ 登录</Subheading>
        <BodyText>当前版本暂未开放，请先使用手机号登录。</BodyText>
      </Card>
      <Button title="返回登录" tone="ghost" onPress={() => router.back()} />
    </Screen>
  );
}
