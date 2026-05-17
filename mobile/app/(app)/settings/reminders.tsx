import * as Clipboard from "expo-clipboard";
import Constants from "expo-constants";
import * as Notifications from "expo-notifications";
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Platform, Switch } from "react-native";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { InlineAlert } from "@/components/ui/inline-alert";
import { Input } from "@/components/ui/input";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading, Subheading } from "@/components/ui/text";
import { REMINDER_DEBUG_COPY } from "@/constants/content";
import { fetchDevices, fetchReminderPreference, registerDevice, triggerReminder, updateReminderPreference } from "@/lib/api/emotions";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

type NoticeTone = "info" | "warning" | "danger";

function withTimeout<T>(promise: Promise<T>, timeoutMs: number, message: string) {
  return Promise.race<T>([
    promise,
    new Promise<T>((_, reject) => {
      setTimeout(() => reject(new Error(message)), timeoutMs);
    }),
  ]);
}

function resolveProjectId() {
  const extra = Constants.expoConfig?.extra as { eas?: { projectId?: string } } | undefined;
  return Constants.easConfig?.projectId ?? extra?.eas?.projectId;
}

async function getExpoPushTokenAsync() {
  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("default", {
      name: "default",
      importance: Notifications.AndroidImportance.MAX,
    });
  }

  const currentPermissions = await Notifications.getPermissionsAsync();
  let finalStatus = currentPermissions.status;

  if (finalStatus !== "granted") {
    const requestedPermissions = await Notifications.requestPermissionsAsync();
    finalStatus = requestedPermissions.status;
  }

  if (finalStatus !== "granted") {
    throw new Error("还没有获得通知权限，请先允许应用发送通知。");
  }

  const projectId = resolveProjectId();
  if (!projectId) {
    throw new Error("当前应用还没有配置 Expo projectId，暂时无法获取设备令牌。");
  }
  const tokenResponse = projectId
    ? await withTimeout(
        Notifications.getExpoPushTokenAsync({
          projectId,
          applicationId: Constants.expoConfig?.android?.package,
        }),
        15000,
        "获取设备令牌超时，请稍后重试。",
      )
    : await withTimeout(Notifications.getExpoPushTokenAsync(), 15000, "获取设备令牌超时，请稍后重试。");

  if (!tokenResponse.data) {
    throw new Error("没有拿到有效的设备令牌。");
  }

  return tokenResponse.data;
}

function inferPlatform(): "ios" | "android" | "web" {
  if (Platform.OS === "ios") {
    return "ios";
  }
  if (Platform.OS === "web") {
    return "web";
  }
  return "android";
}

function buildDefaultDeviceId() {
  const sessionId = Constants.sessionId ? Constants.sessionId.slice(0, 8) : "device";
  return `${inferPlatform()}-expo-${sessionId}`;
}

export default function ReminderSettingsScreen() {
  const queryClient = useQueryClient();
  const prefQuery = useQuery({
    queryKey: ["reminder-preference"],
    queryFn: fetchReminderPreference,
  });
  const devicesQuery = useQuery({
    queryKey: ["devices"],
    queryFn: fetchDevices,
  });

  const [enabled, setEnabled] = useState(false);
  const [timezone, setTimezone] = useState("Asia/Shanghai");
  const [reminderTime, setReminderTime] = useState("09:00:00");
  const [quietStart, setQuietStart] = useState("23:00:00");
  const [quietEnd, setQuietEnd] = useState("07:00:00");
  const [frequencyPerDay, setFrequencyPerDay] = useState("1");
  const [preferredTypes, setPreferredTypes] = useState("phrase");
  const [deviceToken, setDeviceToken] = useState("");
  const [deviceId, setDeviceId] = useState(buildDefaultDeviceId());
  const [notice, setNotice] = useState<{ message: string; tone: NoticeTone } | null>(null);
  const [registerStage, setRegisterStage] = useState("");

  useEffect(() => {
    if (!prefQuery.data) {
      return;
    }
    setEnabled(prefQuery.data.enabled);
    setTimezone(prefQuery.data.timezone);
    setReminderTime(prefQuery.data.reminder_time);
    setQuietStart(prefQuery.data.quiet_hours_start);
    setQuietEnd(prefQuery.data.quiet_hours_end);
    setFrequencyPerDay(String(prefQuery.data.frequency_per_day));
    setPreferredTypes(prefQuery.data.preferred_content_types.join(","));
  }, [prefQuery.data]);

  const updateMutation = useMutation({
    mutationFn: () =>
      updateReminderPreference({
        enabled,
        timezone,
        reminder_time: reminderTime,
        quiet_hours_start: quietStart,
        quiet_hours_end: quietEnd,
        frequency_per_day: Math.max(1, Number(frequencyPerDay) || 1),
        preferred_content_types: preferredTypes
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      }),
    onSuccess: async () => {
      setNotice({ message: "提醒设置已保存。", tone: "info" });
      await queryClient.invalidateQueries({ queryKey: ["reminder-preference"] });
    },
    onError: () => {
      setNotice({ message: "提醒设置保存失败，请稍后重试。", tone: "danger" });
    },
  });

  const registerMutation = useMutation({
    mutationFn: registerDevice,
    onSuccess: async (device) => {
      setRegisterStage("");
      setDeviceToken(device.token);
      setNotice({ message: "当前设备已完成登记，现在可以尝试发送提醒。", tone: "info" });
      await queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
    onError: () => {
      setRegisterStage("");
      setNotice({ message: "设备登记失败，请检查网络后再试。", tone: "danger" });
    },
  });

  const autoRegisterMutation = useMutation({
    mutationFn: async () => {
      setRegisterStage("正在请求通知权限...");
      setNotice({ message: "正在请求通知权限并获取设备令牌，请稍候。", tone: "info" });
      const token = await getExpoPushTokenAsync();
      setRegisterStage("正在登记当前设备...");
      setDeviceToken(token);
      return registerMutation.mutateAsync({
        token,
        platform: inferPlatform(),
        device_id: deviceId,
      });
    },
    onError: (error) => {
      setRegisterStage("");
      const message = error instanceof Error ? error.message : "暂时无法获取通知权限或设备令牌。";
      setNotice({ message, tone: "warning" });
    },
  });

  const triggerMutation = useMutation({
    mutationFn: triggerReminder,
    onSuccess: (logs) => {
      if (logs.length === 0) {
        setNotice({ message: "还没有生成提醒记录，请先开启提醒并完成设备登记。", tone: "warning" });
        return;
      }
      const provider = String(logs[0]?.response_payload?.provider ?? "");
      setNotice({
        message: provider === "expo" ? "提醒已发送到 Expo Go，请留意手机通知。" : `提醒已生成，当前通道：${provider || "mock"}`,
        tone: "info",
      });
    },
    onError: () => {
      setNotice({ message: "提醒发送失败，请稍后重试。", tone: "danger" });
    },
  });

  const triggerResult = triggerMutation.data ?? [];
  const triggerHint =
    triggerMutation.isSuccess && triggerResult.length === 0
      ? "暂时没有生成提醒记录，通常表示提醒未开启，或当前设备还没有完成登记。"
      : triggerMutation.isSuccess
        ? `本次已生成 ${triggerResult.length} 条提醒记录。`
        : "";

  return (
    <Screen>
      <Heading>提醒设置</Heading>
      <InlineAlert message={REMINDER_DEBUG_COPY} tone="warning" />
      {notice ? <InlineAlert message={notice.message} tone={notice.tone} /> : null}
      <Card style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
        <BodyText>开启提醒</BodyText>
        <Switch value={enabled} onValueChange={setEnabled} />
      </Card>
      <Input label="时区" value={timezone} onChangeText={setTimezone} />
      <Input label="提醒时间" value={reminderTime} onChangeText={setReminderTime} />
      <Input label="免打扰开始时间" value={quietStart} onChangeText={setQuietStart} />
      <Input label="免打扰结束时间" value={quietEnd} onChangeText={setQuietEnd} />
      <Input label="每天提醒次数" value={frequencyPerDay} onChangeText={setFrequencyPerDay} keyboardType="number-pad" />
      <Input label="偏好内容类型" value={preferredTypes} onChangeText={setPreferredTypes} placeholder="例如：phrase,article,music" />
      <Button title="保存提醒设置" onPress={() => updateMutation.mutate()} loading={updateMutation.isPending} />

      <Card>
        <Subheading>当前设备</Subheading>
        <BodyText>使用 Expo Go 时，可以先获取通知权限并自动登记当前手机。</BodyText>
        <BodyText>当前 Project ID：{resolveProjectId() ?? "未配置"}</BodyText>
        {registerStage ? <BodyText>{registerStage}</BodyText> : null}
      </Card>
      <Input label="设备令牌" value={deviceToken} onChangeText={setDeviceToken} placeholder="获取成功后会自动填入 Expo push token" />
      <Input label="设备标识" value={deviceId} onChangeText={setDeviceId} />
      <Button title="获取权限并登记当前设备" onPress={() => autoRegisterMutation.mutate()} loading={autoRegisterMutation.isPending} />
      <Button
        title="使用当前令牌重新登记"
        tone="soft"
        onPress={() =>
          registerMutation.mutate({
            token: deviceToken,
            platform: inferPlatform(),
            device_id: deviceId,
          })
        }
        loading={registerMutation.isPending}
        disabled={!deviceToken.trim()}
      />

      <Card>
        <Subheading>已登记设备</Subheading>
        {(devicesQuery.data ?? []).map((item) => (
          <BodyText key={item.id}>
            {item.platform} | {item.device_id} | {item.token}
          </BodyText>
        ))}
      </Card>
      <Button title="立即生成一次提醒" onPress={() => triggerMutation.mutate()} loading={triggerMutation.isPending} />
      {triggerHint ? <InlineAlert message={triggerHint} /> : null}
      <Button
        title="复制最近一次提醒内容"
        tone="ghost"
        onPress={() => void Clipboard.setStringAsync(JSON.stringify(triggerResult[0]?.payload ?? {}, null, 2))}
      />
    </Screen>
  );
}
