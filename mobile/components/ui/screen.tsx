import { LinearGradient } from "expo-linear-gradient";
import { SafeAreaView } from "react-native-safe-area-context";
import { ScrollView, StyleSheet, View } from "react-native";

import { colors, spacing } from "@/constants/theme";

type ScreenProps = {
  children: React.ReactNode;
  scrollable?: boolean;
};

export function Screen({ children, scrollable = true }: ScreenProps) {
  const content = scrollable ? (
    <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      {children}
    </ScrollView>
  ) : (
    <View style={styles.content}>{children}</View>
  );

  return (
    <LinearGradient colors={["#FFF3EA", colors.canvas]} style={styles.gradient}>
      <SafeAreaView style={styles.safeArea}>{content}</SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradient: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  content: {
    padding: spacing.md,
    gap: spacing.md,
    paddingBottom: spacing.xxl,
  },
});
