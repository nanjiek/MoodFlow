import { PropsWithChildren } from "react";
import { Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { colors } from "@/constants/theme";

type AppShellProps = PropsWithChildren<{
  eyebrow: string;
  title: string;
  description: string;
}>;

export function AppShell({ children, description, eyebrow, title }: AppShellProps) {
  return (
    <SafeAreaView edges={["top", "left", "right"]} style={{ flex: 1, backgroundColor: colors.canvas }}>
      <View style={{ flex: 1, paddingHorizontal: 20, paddingTop: 28, paddingBottom: 20, gap: 20 }}>
        <View style={{ gap: 10 }}>
          <Text
            style={{
              color: colors.brandDeep,
              fontSize: 13,
              fontWeight: "700",
              letterSpacing: 1.2,
              textTransform: "uppercase",
            }}
          >
            {eyebrow}
          </Text>
          <Text style={{ color: colors.ink, fontSize: 30, fontWeight: "700", lineHeight: 38 }}>
            {title}
          </Text>
          <Text style={{ color: colors.inkMuted, fontSize: 16, lineHeight: 24 }}>
            {description}
          </Text>
        </View>
        {children}
      </View>
    </SafeAreaView>
  );
}
