import { StyleSheet, Text, TextInput, View, type TextInputProps } from "react-native";

import { colors, radius, spacing, typography } from "@/constants/theme";

export function Input({
  label,
  error,
  multiline,
  ...props
}: TextInputProps & {
  label: string;
  error?: string;
}) {
  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        placeholderTextColor={colors.inkSoft}
        multiline={multiline}
        style={[styles.input, multiline ? styles.multiline : null, error ? styles.inputError : null]}
        {...props}
      />
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    gap: spacing.xs,
  },
  label: {
    color: colors.ink,
    fontSize: typography.caption,
    fontWeight: "700",
  },
  input: {
    minHeight: 52,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    paddingHorizontal: spacing.md,
    color: colors.ink,
    fontSize: typography.body,
  },
  multiline: {
    minHeight: 120,
    paddingTop: spacing.md,
    textAlignVertical: "top",
  },
  inputError: {
    borderColor: colors.danger,
  },
  error: {
    color: colors.danger,
    fontSize: typography.tiny,
  },
});
