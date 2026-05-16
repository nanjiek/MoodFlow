import { FontAwesome6 } from "@expo/vector-icons";
import { Tabs } from "expo-router";

import { colors } from "@/constants/theme";

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.brandDeep,
        tabBarInactiveTintColor: colors.inkSoft,
        tabBarStyle: {
          height: 68,
          paddingTop: 6,
          paddingBottom: 8,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "首页",
          tabBarIcon: ({ color }) => <FontAwesome6 name="house" size={18} color={color} />,
        }}
      />
      <Tabs.Screen
        name="records"
        options={{
          title: "记录",
          tabBarIcon: ({ color }) => <FontAwesome6 name="book-open" size={18} color={color} />,
        }}
      />
      <Tabs.Screen
        name="growth"
        options={{
          title: "成长",
          tabBarIcon: ({ color }) => <FontAwesome6 name="chart-line" size={18} color={color} />,
        }}
      />
      <Tabs.Screen
        name="me"
        options={{
          title: "我的",
          tabBarIcon: ({ color }) => <FontAwesome6 name="user" size={18} color={color} />,
        }}
      />
    </Tabs>
  );
}
