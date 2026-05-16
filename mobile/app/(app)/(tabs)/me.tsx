import { router } from "expo-router";
import { useQuery } from "@tanstack/react-query";

import { MenuRow } from "@/components/app/menu-row";
import { Card } from "@/components/ui/card";
import { Screen } from "@/components/ui/screen";
import { BodyText, Heading, Subheading } from "@/components/ui/text";
import { useAuth } from "@/hooks/useAuth";
import { fetchDevices, fetchReminderPreference } from "@/lib/api/emotions";

export default function MeTabScreen() {
  const { profile, signOut } = useAuth();
  const reminderQuery = useQuery({
    queryKey: ["reminder-preference"],
    queryFn: fetchReminderPreference,
  });
  const devicesQuery = useQuery({
    queryKey: ["devices"],
    queryFn: fetchDevices,
  });

  return (
    <Screen>
      <Heading>我的</Heading>
      <Card>
        <Subheading>{profile?.nickname ?? "MoodFlow 用户"}</Subheading>
        <BodyText>{profile?.phone}</BodyText>
        <BodyText>{profile?.signature || "还没有留下个人签名。"} </BodyText>
      </Card>
      <MenuRow title="个人资料" subtitle="修改昵称、签名、邮箱等" onPress={() => router.push("/(app)/settings/profile")} />
      <MenuRow title="隐私设置" subtitle="匿名模式与情绪加密" onPress={() => router.push("/(app)/settings/privacy")} />
      <MenuRow
        title="设备与提醒设置"
        subtitle={`提醒${reminderQuery.data?.enabled ? "已开启" : "未开启"} · 设备 ${devicesQuery.data?.length ?? 0} 台`}
        onPress={() => router.push("/(app)/settings/reminders")}
      />
      <MenuRow title="数据导出" subtitle="JSON / CSV 同步导出" onPress={() => router.push("/(app)/settings/export")} />
      <MenuRow title="退出登录" subtitle="清除本地会话并回到登录流" onPress={() => void signOut()} />
    </Screen>
  );
}
