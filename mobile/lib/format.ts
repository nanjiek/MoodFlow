export function formatDateTime(value?: string | null) {
  if (!value) {
    return "未设置";
  }
  const date = new Date(value);
  return `${date.getMonth() + 1}月${date.getDate()}日 ${date.getHours().toString().padStart(2, "0")}:${date
    .getMinutes()
    .toString()
    .padStart(2, "0")}`;
}

export function formatDate(value?: string | null) {
  if (!value) {
    return "未设置";
  }
  const date = new Date(value);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

export function fieldErrorText(value: unknown) {
  if (Array.isArray(value)) {
    return value.join(" ");
  }
  return typeof value === "string" ? value : "";
}
