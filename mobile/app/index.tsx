import { Redirect } from "expo-router";

import { useAuth } from "@/hooks/useAuth";
import { Screen } from "@/components/ui/screen";
import { BrandHero } from "@/components/app/brand-hero";

export default function IndexScreen() {
  const { status, bootstrapComplete } = useAuth();

  if (!bootstrapComplete || status === "unknown") {
    return (
      <Screen scrollable={false}>
        <BrandHero title="正在整理你的情绪空间…" description="我们在同步本地会话和最新资料。" />
      </Screen>
    );
  }

  if (status === "authenticated") {
    return <Redirect href="/(app)/(tabs)" />;
  }

  return <Redirect href="/(auth)/login" />;
}
