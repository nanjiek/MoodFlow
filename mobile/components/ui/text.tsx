import { StyleSheet, Text, type TextProps } from "react-native";

import { colors, typography } from "@/constants/theme";

export function Heading(props: TextProps) {
  return <Text {...props} style={[styles.heading, props.style]} />;
}

export function Subheading(props: TextProps) {
  return <Text {...props} style={[styles.subheading, props.style]} />;
}

export function BodyText(props: TextProps) {
  return <Text {...props} style={[styles.body, props.style]} />;
}

export function CaptionText(props: TextProps) {
  return <Text {...props} style={[styles.caption, props.style]} />;
}

const styles = StyleSheet.create({
  heading: {
    color: colors.ink,
    fontSize: typography.hero,
    lineHeight: typography.hero * 1.2,
    fontWeight: "800",
  },
  subheading: {
    color: colors.ink,
    fontSize: typography.subtitle,
    fontWeight: "700",
  },
  body: {
    color: colors.inkMuted,
    fontSize: typography.body,
    lineHeight: typography.body * 1.5,
  },
  caption: {
    color: colors.inkSoft,
    fontSize: typography.caption,
    lineHeight: typography.caption * 1.4,
  },
});
