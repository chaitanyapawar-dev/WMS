import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, use, useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { authApi } from "@/lib/api";
import { getToken } from "@/lib/api/client";
import type { Role, User } from "@/types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  hasRole: (roles: Role[]) => boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [token, setTokenState] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setTokenState(getToken());
    setHydrated(true);
  }, []);

  const { data: user, isLoading } = useQuery({
    queryKey: ["current-user", token],
    queryFn: () => authApi.getCurrentUser(token!),
    enabled: hydrated && Boolean(token),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const signIn = useCallback(async (email: string, password: string) => {
    const { access_token } = await authApi.login({ email, password });
    setTokenState(access_token);
  }, []);

  const signOut = useCallback(() => {
    authApi.logout();
    setTokenState(null);
    queryClient.clear();
  }, [queryClient]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: user ?? null,
      isLoading: !hydrated || (Boolean(token) && isLoading),
      isAuthenticated: Boolean(user),
      hasRole: (roles: Role[]) => Boolean(user && roles.includes(user.role)),
      signIn,
      signOut,
    }),
    [user, hydrated, token, isLoading, signIn, signOut],
  );

  return <AuthContext value={value}>{children}</AuthContext>;
}

export function useAuth() {
  const context = use(AuthContext);
  if (!context) throw new Error("useAuth must be used inside <AuthProvider>");
  return context;
}
