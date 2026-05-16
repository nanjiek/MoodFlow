import { apiRequest } from "@/lib/api/client";
import type { AuthPayload, PasswordResetSendResult, PasswordResetVerifyResult, SocialAccount, UserProfile } from "@/types/domain";

export async function login(phone: string, password: string) {
  const response = await apiRequest<AuthPayload>("/api/auth/login/", {
    method: "POST",
    body: { phone, password },
  });
  return response.data;
}

export async function register(phone: string, password: string, nickname: string) {
  const response = await apiRequest<AuthPayload>("/api/auth/register/", {
    method: "POST",
    body: { phone, password, nickname },
  });
  return response.data;
}

export async function logout() {
  const response = await apiRequest<{ detail: string }>("/api/auth/logout/", {
    method: "POST",
  });
  return response.data;
}

export async function fetchProfile() {
  const response = await apiRequest<UserProfile>("/api/me/");
  return response.data;
}

export async function updateProfile(body: Partial<UserProfile>) {
  const response = await apiRequest<UserProfile>("/api/me/", {
    method: "PATCH",
    body,
  });
  return response.data;
}

export async function fetchPrivacy() {
  const response = await apiRequest<UserProfile["privacy"]>("/api/me/privacy/");
  return response.data;
}

export async function updatePrivacy(body: UserProfile["privacy"]) {
  const response = await apiRequest<UserProfile["privacy"]>("/api/me/privacy/", {
    method: "PATCH",
    body,
  });
  return response.data;
}

export async function fetchSocialBindings() {
  const response = await apiRequest<SocialAccount[]>("/api/me/social-bindings/");
  return response.data;
}

export async function sendPasswordResetCode(phone: string) {
  const response = await apiRequest<PasswordResetSendResult>("/api/auth/password-reset/send-code/", {
    method: "POST",
    body: { phone },
  });
  return response.data;
}

export async function verifyPasswordResetCode(phone: string, requestId: string, code: string) {
  const response = await apiRequest<PasswordResetVerifyResult>("/api/auth/password-reset/verify-code/", {
    method: "POST",
    body: { phone, request_id: requestId, code },
  });
  return response.data;
}

export async function resetPassword(phone: string, requestId: string, code: string, newPassword: string) {
  const response = await apiRequest<Record<string, never>>("/api/auth/password-reset/reset/", {
    method: "POST",
    body: { phone, request_id: requestId, code, new_password: newPassword },
  });
  return response.data;
}
