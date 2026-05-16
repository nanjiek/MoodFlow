import { Link, Stack } from "expo-router";
import { Text, View } from "react-native";

import { colors } from "@/constants/theme";

export default function NotFoundScreen() {
  return (
    <>
      <Stack.Screen options={{ title: "Not found" }} />
      <View
        style={{
          flex: 1,
          alignItems: "center",
          justifyContent: "center",
          gap: 12,
          backgroundColor: colors.canvas,
          padding: 24,
        }}
      >
        <Text style={{ color: colors.ink, fontSize: 22, fontWeight: "700" }}>
          This route does not exist.
        </Text>
        <Link href="/" style={{ color: colors.brandDeep, fontSize: 16 }}>
          Return home
        </Link>
      </View>
    </>
  );
}
