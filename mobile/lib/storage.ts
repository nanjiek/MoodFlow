import AsyncStorage from "@react-native-async-storage/async-storage";

import type { UserProfile } from "@/types/domain";

const keys = {
  token: "moodflow.token",
  profile: "moodflow.profile",
  firstLaunch: "moodflow.first-launch",
  recordDraft: "moodflow.record-draft",
};

export async function getStoredToken() {
  return AsyncStorage.getItem(keys.token);
}

export async function setStoredToken(token: string | null) {
  if (!token) {
    await AsyncStorage.removeItem(keys.token);
    return;
  }
  await AsyncStorage.setItem(keys.token, token);
}

export async function getStoredProfile() {
  const raw = await AsyncStorage.getItem(keys.profile);
  return raw ? (JSON.parse(raw) as UserProfile) : null;
}

export async function setStoredProfile(profile: UserProfile | null) {
  if (!profile) {
    await AsyncStorage.removeItem(keys.profile);
    return;
  }
  await AsyncStorage.setItem(keys.profile, JSON.stringify(profile));
}

export async function getFirstLaunchSeen() {
  return (await AsyncStorage.getItem(keys.firstLaunch)) === "1";
}

export async function setFirstLaunchSeen() {
  await AsyncStorage.setItem(keys.firstLaunch, "1");
}

export async function getRecordDraft() {
  return AsyncStorage.getItem(keys.recordDraft);
}

export async function setRecordDraft(value: string | null) {
  if (!value) {
    await AsyncStorage.removeItem(keys.recordDraft);
    return;
  }
  await AsyncStorage.setItem(keys.recordDraft, value);
}
