import { router } from "expo-router";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading, Subheading } from "@/components/ui/text";
import { SOCIAL_PLACEHOLDER_COPY } from "@/constants/content";

export default function SocialLoginPlaceholderScreen() {
  return (
    <Screen>
      <Heading>Social Login</Heading>
      <BodyText>{SOCIAL_PLACEHOLDER_COPY.description}</BodyText>
      <Card>
        <Subheading>WeChat</Subheading>
        <BodyText>The entry is reserved, but the first version does not fake a successful OAuth flow.</BodyText>
      </Card>
      <Card>
        <Subheading>QQ</Subheading>
        <BodyText>This path stays in placeholder mode until the real code exchange is wired.</BodyText>
      </Card>
      <Button title="Back To Login" tone="ghost" onPress={() => router.back()} />
    </Screen>
  );
}
