import type { EmotionCode } from "@/constants/emotions";

export type SocialAccount = {
  id: number;
  provider: "wechat" | "qq";
  open_id: string;
  union_id: string;
  app_id: string;
  nickname: string;
  avatar_url: string;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
};

export type UserProfile = {
  id: number;
  external_id: string;
  nickname: string;
  avatar_url: string;
  gender: "male" | "female" | "unknown";
  birth_date: string | null;
  phone: string;
  email: string;
  signature: string;
  anonymous_mode: boolean;
  emotion_encryption_enabled: boolean;
  privacy: {
    anonymous_mode: boolean;
    emotion_encryption_enabled: boolean;
  };
  social_accounts: SocialAccount[];
  created_at: string;
  updated_at: string;
};

export type AuthPayload = {
  token: string;
  token_type: "Bearer";
  expires_at: string;
  profile: UserProfile;
};

export type PasswordResetSendResult = {
  request_id: string;
  expires_at: string;
  phone: string;
  cooldown_seconds: number;
  debug_code?: string;
};

export type PasswordResetVerifyResult = {
  request_id: string;
  verified: boolean;
  phone: string;
  expires_at?: string;
};

export type EmotionPresentation = {
  code: EmotionCode;
  name: string;
  display_name: string;
  display_hint: string;
  energy: "high" | "medium" | "low";
  valence: "positive" | "negative" | "neutral";
  companion_focus?: string[];
};

export type CompanionItem = {
  id: number;
  content_type: string;
  emotion_tag?: number | null;
  emotion_tag_detail?: { id: number; code?: string; name?: string } | null;
  title: string;
  body: string;
  resource_url: string;
  weight?: number;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
};

export type EmotionAnalysis = {
  id: number;
  record?: number;
  record_id: number;
  user_id?: number;
  selected_label: EmotionCode;
  predicted_label: EmotionCode;
  confidence: number;
  keywords: string[];
  intensity: number;
  trend: string;
  cause: string;
  predicted_label_detail: EmotionPresentation;
  explanation: string;
  gentle_feedback: string;
  companion_suggestions: CompanionItem[];
  model_version: string;
  raw_result?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type EmotionRecord = {
  id: number;
  emotion_text: string;
  text: string;
  selected_label: EmotionCode;
  emoji_id: string;
  recorded_at: string;
  is_collect: boolean;
  is_encrypted: boolean;
  source: string;
  analysis?: EmotionAnalysis;
  created_at: string;
  updated_at: string;
};

export type Paginated<T> = {
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type DailyReport = {
  date: string;
  start_at: string;
  end_at: string;
  total_records: number;
  collect_count: number;
  dominant_emotion: EmotionPresentation | null;
  emotion_breakdown: Array<EmotionPresentation & { count: number; ratio: number }>;
  summary: {
    summary: string;
    dominant_emotion: EmotionPresentation | null;
    highlights: string[];
    next_suggestion: string;
  };
  daily_series: Array<{ day: string; count: number }>;
  records: EmotionRecord[];
};

export type WeeklyReport = DailyReport & {
  start_date: string;
  end_date: string;
};

export type GrowthCurve = {
  start_date: string;
  end_date: string;
  days: number;
  summary: {
    record_count: number;
    average_score: number;
    dominant_emotion: EmotionPresentation | null;
    trend: string;
  };
  series: Array<{
    date: string;
    score: number;
    average_intensity: number;
    record_count: number;
    dominant_emotion: EmotionPresentation | null;
    emotion_breakdown: Array<EmotionPresentation & { count: number; ratio: number }>;
    positive_count: number;
    negative_count: number;
    neutral_count: number;
    delta: number | null;
  }>;
  drilldown?: {
    date: string;
    record_count: number;
    records: Array<{
      id: number;
      recorded_at: string;
      emotion_text: string;
      source: string;
      is_collect: boolean;
      tag: EmotionPresentation;
      analysis_label: EmotionPresentation;
      intensity: number;
      score: number;
    }>;
  };
};

export type ReminderPreference = {
  enabled: boolean;
  timezone: string;
  reminder_time: string;
  quiet_hours_start: string;
  quiet_hours_end: string;
  frequency_per_day: number;
  preferred_content_types: string[];
  last_triggered_at: string | null;
  created_at: string;
  updated_at: string;
};

export type DeviceToken = {
  id: number;
  token: string;
  platform: string;
  device_id: string;
  is_active: boolean;
  last_seen_at: string;
  created_at: string;
  updated_at: string;
};

export type ReminderDispatchLog = {
  id: number;
  status: string;
  payload: Record<string, unknown>;
  response_payload: Record<string, unknown>;
  attempt_count: number;
  last_error: string;
  next_retry_at: string | null;
  sent_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ExportTask = {
  id: number;
  file_format: "json" | "csv";
  status: string;
  start_at: string;
  end_at: string;
  record_count: number;
  file_name: string;
  metadata: Record<string, unknown>;
  error_message: string;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  content?: string;
};

export type CompanionRecommendations = {
  emotion: EmotionPresentation;
  emotion_source: string;
  preferred_types: string[];
  recommendations: CompanionItem[];
};
