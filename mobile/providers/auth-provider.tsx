import { createContext, useEffect, useMemo, useState } from "react";

import { registerUnauthorizedHandler } from "@/lib/api/client";
import { fetchProfile, login as loginApi, logout as logoutApi, register as registerApi } from "@/lib/api/auth";
import { getStoredProfile, getStoredToken, setStoredProfile, setStoredToken } from "@/lib/storage";
import type { UserProfile } from "@/types/domain";

type AuthStatus = "unknown" | "anonymous" | "authenticated";

type AuthContextValue = {
  status: AuthStatus;
  token: string | null;
  profile: UserProfile | null;
  bootstrapComplete: boolean;
  signIn: (phone: string, password: string) => Promise<void>;
  signUp: (phone: string, password: string, nickname: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  updateCachedProfile: (profile: UserProfile | null) => Promise<void>;
};

export const AuthContext = createContext<AuthContextValue>({
  status: "unknown",
  token: null,
  profile: null,
  bootstrapComplete: false,
  signIn: async () => undefined,
  signUp: async () => undefined,
  signOut: async () => undefined,
  refreshProfile: async () => undefined,
  updateCachedProfile: async () => undefined,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("unknown");
  const [token, setToken] = useState<string | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [bootstrapComplete, setBootstrapComplete] = useState(false);

  useEffect(() => {
    registerUnauthorizedHandler(async () => {
      setToken(null);
      setProfile(null);
      setStatus("anonymous");
      await setStoredToken(null);
      await setStoredProfile(null);
    });
  }, []);

  useEffect(() => {
    async function bootstrap() {
      const cachedToken = await getStoredToken();
      const cachedProfile = await getStoredProfile();
      if (!cachedToken) {
        setStatus("anonymous");
        setBootstrapComplete(true);
        return;
      }
      setToken(cachedToken);
      setProfile(cachedProfile);
      try {
        const freshProfile = await fetchProfile();
        setProfile(freshProfile);
        await setStoredProfile(freshProfile);
        setStatus("authenticated");
      } catch {
        setToken(null);
        setProfile(null);
        await setStoredToken(null);
        await setStoredProfile(null);
        setStatus("anonymous");
      } finally {
        setBootstrapComplete(true);
      }
    }
    void bootstrap();
  }, []);

  const updateCachedProfile = async (nextProfile: UserProfile | null) => {
    setProfile(nextProfile);
    await setStoredProfile(nextProfile);
  };

  const signIn = async (phone: string, password: string) => {
    const auth = await loginApi(phone, password);
    await setStoredToken(auth.token);
    await setStoredProfile(auth.profile);
    setToken(auth.token);
    setProfile(auth.profile);
    setStatus("authenticated");
  };

  const signUp = async (phone: string, password: string, nickname: string) => {
    const auth = await registerApi(phone, password, nickname);
    await setStoredToken(auth.token);
    await setStoredProfile(auth.profile);
    setToken(auth.token);
    setProfile(auth.profile);
    setStatus("authenticated");
  };

  const signOut = async () => {
    try {
      await logoutApi();
    } catch {
      // The local session should still be cleared even if the backend token has expired.
    }
    setToken(null);
    setProfile(null);
    setStatus("anonymous");
    await setStoredToken(null);
    await setStoredProfile(null);
  };

  const refreshProfile = async () => {
    const nextProfile = await fetchProfile();
    await updateCachedProfile(nextProfile);
  };

  const value = useMemo(
    () => ({
      status,
      token,
      profile,
      bootstrapComplete,
      signIn,
      signUp,
      signOut,
      refreshProfile,
      updateCachedProfile,
    }),
    [bootstrapComplete, profile, status, token],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
