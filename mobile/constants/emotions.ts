import { colors } from "@/constants/theme";

export type EmotionCode =
  | "happy"
  | "calm"
  | "expecting"
  | "anxious"
  | "sad"
  | "irritable"
  | "plain"
  | "tired";

export const EMOTION_OPTIONS: Array<{
  code: EmotionCode;
  label: string;
  description: string;
  emoji: string;
  tint: string;
}> = [
  { code: "happy", label: "开心", description: "今天挺开心", emoji: "😊", tint: "#F7C97A" },
  { code: "calm", label: "平静", description: "心里比较稳", emoji: "🌿", tint: colors.mint },
  { code: "expecting", label: "期待", description: "有点盼头", emoji: "✨", tint: "#F7D0C5" },
  { code: "anxious", label: "焦虑", description: "脑子停不下来", emoji: "😵", tint: "#F2C1A4" },
  { code: "sad", label: "难过", description: "心里低落", emoji: "🌧️", tint: "#C8D6F0" },
  { code: "irritable", label: "烦躁", description: "事情很多很挤", emoji: "🔥", tint: "#F0C0B8" },
  { code: "plain", label: "平淡", description: "没什么波动", emoji: "☁️", tint: "#D9DEE7" },
  { code: "tired", label: "疲惫", description: "像没电了一样", emoji: "🛋️", tint: "#D9D0C7" },
];

export const EMOTION_BY_CODE = Object.fromEntries(
  EMOTION_OPTIONS.map((item) => [item.code, item]),
) as Record<EmotionCode, (typeof EMOTION_OPTIONS)[number]>;
