import * as Clipboard from "expo-clipboard";
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Switch } from "react-native";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { InlineAlert } from "@/components/ui/inline-alert";
import { Input } from "@/components/ui/input";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading, Subheading } from "@/components/ui/text";
import { REMINDER_DEBUG_COPY } from "@/constants/content";
import { fetchDevices, fetchReminderPreference, registerDevice, triggerReminder, updateReminderPreference } from "@/lib/api/emotions";

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
  const [deviceToken, setDeviceToken] = useState("expo-debug-token");
  const [deviceId, setDeviceId] = useState("simulator");

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
      await queryClient.invalidateQueries({ queryKey: ["reminder-preference"] });
    },
  });

  const registerMutation = useMutation({
    mutationFn: () => registerDevice({ token: deviceToken, platform: "android", device_id: deviceId }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
  });

  const triggerMutation = useMutation({
    mutationFn: triggerReminder,
  });

  const triggerResult = triggerMutation.data ?? [];
  const triggerHint =
    triggerMutation.isSuccess && triggerResult.length === 0
      ? "The API returned an empty list. That usually means reminders are disabled or there is no active device token."
      : triggerMutation.isSuccess
        ? `Triggered ${triggerResult.length} reminder log entries.`
        : "";

  return (
    <Screen>
      <Heading>Reminder Settings</Heading>
      <InlineAlert message={REMINDER_DEBUG_COPY} tone="warning" />
      <Card style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
        <BodyText>Enabled</BodyText>
        <Switch value={enabled} onValueChange={setEnabled} />
      </Card>
      <Input label="Timezone" value={timezone} onChangeText={setTimezone} />
      <Input label="Reminder Time" value={reminderTime} onChangeText={setReminderTime} />
      <Input label="Quiet Hours Start" value={quietStart} onChangeText={setQuietStart} />
      <Input label="Quiet Hours End" value={quietEnd} onChangeText={setQuietEnd} />
      <Input label="Frequency Per Day" value={frequencyPerDay} onChangeText={setFrequencyPerDay} keyboardType="number-pad" />
      <Input label="Preferred Content Types" value={preferredTypes} onChangeText={setPreferredTypes} placeholder="phrase,article,music" />
      <Button title="Save Preference" onPress={() => updateMutation.mutate()} loading={updateMutation.isPending} />
      <Input label="Device Token" value={deviceToken} onChangeText={setDeviceToken} />
      <Input label="Device ID" value={deviceId} onChangeText={setDeviceId} />
      <Button title="Register Debug Device" onPress={() => registerMutation.mutate()} loading={registerMutation.isPending} />
      <Card>
        <Subheading>Registered Devices</Subheading>
        {(devicesQuery.data ?? []).map((item) => (
          <BodyText key={item.id}>
            {item.platform} | {item.device_id} | {item.token}
          </BodyText>
        ))}
      </Card>
      <Button title="Trigger Reminder Now" onPress={() => triggerMutation.mutate()} loading={triggerMutation.isPending} />
      {triggerHint ? <InlineAlert message={triggerHint} /> : null}
      <Button
        title="Copy Latest Payload"
        tone="ghost"
        onPress={() => void Clipboard.setStringAsync(JSON.stringify(triggerResult[0]?.payload ?? {}, null, 2))}
      />
    </Screen>
  );
}
