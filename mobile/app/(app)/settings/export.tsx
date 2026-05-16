import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { InlineAlert } from "@/components/ui/inline-alert";
import { Input } from "@/components/ui/input";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading, Subheading } from "@/components/ui/text";
import { EXPORT_COPY } from "@/constants/content";
import { createExportTask, downloadExport, fetchExportTasks } from "@/lib/api/emotions";

export default function ExportSettingsScreen() {
  const queryClient = useQueryClient();
  const [format, setFormat] = useState<"json" | "csv">("json");
  const [startAt, setStartAt] = useState("2026-05-01T00:00:00+08:00");
  const [endAt, setEndAt] = useState("2026-05-16T23:59:59+08:00");

  const exportQuery = useQuery({
    queryKey: ["exports"],
    queryFn: fetchExportTasks,
  });

  const createMutation = useMutation({
    mutationFn: () => createExportTask({ file_format: format, start_at: startAt, end_at: endAt }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["exports"] });
    },
  });

  const downloadMutation = useMutation({
    mutationFn: async (taskId: number) => {
      const task = await downloadExport(taskId);
      const directory = FileSystem.cacheDirectory ?? FileSystem.documentDirectory ?? "";
      const target = `${directory}${task.file_name}`;
      await FileSystem.writeAsStringAsync(target, task.content ?? "");
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(target);
      }
      return task;
    },
  });

  return (
    <Screen>
      <Heading>Export Data</Heading>
      <InlineAlert message={EXPORT_COPY} />
      <Input label="Format" value={format} onChangeText={(value) => setFormat(value === "csv" ? "csv" : "json")} />
      <Input label="Start At" value={startAt} onChangeText={setStartAt} />
      <Input label="End At" value={endAt} onChangeText={setEndAt} />
      <Button title="Create Export Task" onPress={() => createMutation.mutate()} loading={createMutation.isPending} />
      {(exportQuery.data ?? []).map((task) => (
        <Card key={task.id}>
          <Subheading>{task.file_name}</Subheading>
          <BodyText>
            {task.file_format.toUpperCase()} | {task.status} | {task.record_count} records
          </BodyText>
          <BodyText>{task.completed_at ? `Completed: ${task.completed_at}` : "Processing or already returned inline content"}</BodyText>
          <Button title="Preview And Share" tone="soft" onPress={() => downloadMutation.mutate(task.id)} />
        </Card>
      ))}
    </Screen>
  );
}
