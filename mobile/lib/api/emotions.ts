import { apiRequest } from "@/lib/api/client";
import type {
  CompanionRecommendations,
  DailyReport,
  EmotionAnalysis,
  EmotionRecord,
  ExportTask,
  GrowthCurve,
  Paginated,
  ReminderDispatchLog,
  ReminderPreference,
  WeeklyReport,
} from "@/types/domain";

type RecordFilters = {
  selectedLabel?: string;
  isCollect?: boolean;
  isEncrypted?: boolean;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
};

function withQuery(path: string, params: Record<string, string | number | boolean | undefined>) {
  const url = new URL(path, "http://placeholder.local");
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
  return `${url.pathname}${url.search}`;
}

export async function fetchRecords(filters: RecordFilters = {}) {
  const response = await apiRequest<Paginated<EmotionRecord>>(
    withQuery("/api/emotions/records/", {
      selected_label: filters.selectedLabel,
      is_collect: filters.isCollect,
      is_encrypted: filters.isEncrypted,
      date_from: filters.dateFrom,
      date_to: filters.dateTo,
      page: filters.page,
    }),
  );
  return response.data;
}

export async function fetchHistoryByDay(date: string) {
  const response = await apiRequest<{ date: string; count: number; results: EmotionRecord[] }>(
    `/api/emotions/records/history-by-day/?date=${date}`,
  );
  return response.data;
}

export async function createRecord(body: {
  selected_label: string;
  text?: string;
  emoji_id?: string;
  is_collect?: boolean;
  is_encrypted?: boolean;
  recorded_at?: string;
}) {
  const response = await apiRequest<EmotionRecord>("/api/emotions/records/", {
    method: "POST",
    body,
  });
  return response.data;
}

export async function updateRecord(
  id: number,
  body: {
    selected_label: string;
    text?: string;
    emoji_id?: string;
    is_collect?: boolean;
    is_encrypted?: boolean;
    recorded_at?: string;
  },
) {
  const response = await apiRequest<EmotionRecord>(`/api/emotions/records/${id}/`, {
    method: "PATCH",
    body,
  });
  return response.data;
}

export async function deleteRecord(id: number) {
  const response = await apiRequest<{ id: number; deleted: boolean }>(`/api/emotions/records/${id}/`, {
    method: "DELETE",
  });
  return response.data;
}

export async function toggleFavorite(id: number, isCollect?: boolean) {
  const response = await apiRequest<{ id: number; is_collect: boolean }>(`/api/emotions/records/${id}/favorite/`, {
    method: "POST",
    body: isCollect === undefined ? {} : { is_collect: isCollect },
  });
  return response.data;
}

export async function fetchAnalysis(recordId: number) {
  const response = await apiRequest<EmotionAnalysis>(`/api/emotions/records/${recordId}/analysis/`);
  return response.data;
}

export async function submitAnalysisCorrection(recordId: number, body: { accepted: boolean; corrected_label?: string; note?: string }) {
  const response = await apiRequest<{ analysis_id: number; record_id: number; feedback_saved: boolean; feedback: Record<string, unknown> }>(
    `/api/emotions/records/${recordId}/analysis/correct/`,
    {
      method: "POST",
      body,
    },
  );
  return response.data;
}

export async function fetchCompanionRecommendations(limit = 3) {
  const response = await apiRequest<CompanionRecommendations>(`/api/companion/recommendations/?limit=${limit}`);
  return response.data;
}

export async function fetchDailyReport(date?: string) {
  const response = await apiRequest<DailyReport>(
    date ? `/api/emotions/reports/daily/?date=${date}` : "/api/emotions/reports/daily/",
  );
  return response.data;
}

export async function fetchWeeklyReport(startDate?: string, endDate?: string) {
  const path = withQuery("/api/emotions/reports/weekly/", {
    start_date: startDate,
    end_date: endDate,
  });
  const response = await apiRequest<WeeklyReport>(path);
  return response.data;
}

export async function fetchGrowthCurve(days = 7, date?: string) {
  const path = withQuery("/api/emotions/growth-curve/", {
    days,
    date,
  });
  const response = await apiRequest<GrowthCurve>(path);
  return response.data;
}

export async function fetchReminderPreference() {
  const response = await apiRequest<ReminderPreference>("/api/emotions/reminder-preferences/");
  return response.data;
}

export async function updateReminderPreference(body: Partial<ReminderPreference>) {
  const response = await apiRequest<ReminderPreference>("/api/emotions/reminder-preferences/", {
    method: "PATCH",
    body,
  });
  return response.data;
}

export async function fetchDevices() {
  const response = await apiRequest<Array<{ id: number; token: string; platform: string; device_id: string; is_active: boolean }>>(
    "/api/emotions/devices/",
  );
  return response.data;
}

export async function registerDevice(body: { token: string; platform: string; device_id: string }) {
  const response = await apiRequest<{ id: number; token: string; platform: string; device_id: string; is_active: boolean }>(
    "/api/emotions/devices/",
    {
      method: "POST",
      body,
    },
  );
  return response.data;
}

export async function triggerReminder() {
  const response = await apiRequest<ReminderDispatchLog[]>("/api/emotions/reminders/trigger/", {
    method: "POST",
  });
  return response.data;
}

export async function fetchExportTasks() {
  const response = await apiRequest<ExportTask[]>("/api/emotions/exports/");
  return response.data;
}

export async function createExportTask(body: { file_format: "json" | "csv"; start_at: string; end_at: string }) {
  const response = await apiRequest<ExportTask>("/api/emotions/exports/", {
    method: "POST",
    body,
  });
  return response.data;
}

export async function downloadExport(taskId: number) {
  const response = await apiRequest<ExportTask>(`/api/emotions/exports/${taskId}/download/`);
  return response.data;
}
