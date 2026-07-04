import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { tokenStorage } from "./token-storage";
import { useUsersMe } from "@/api/generated/users/users";
import type { User } from "@/api/generated/models";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (accessToken: string, refreshToken: string, user: User) => void;
  logout: () => void;
  setUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<User | null>(null);
  const [isInitializing, setIsInitializing] = useState<boolean>(() => {
    return tokenStorage.getAccessToken() !== null;
  });

  const meQuery = useUsersMe({
    query: {
      enabled: tokenStorage.getAccessToken() !== null,
      retry: false,
      staleTime: 5 * 60 * 1000,
    },
  });

  useEffect(() => {
    if (meQuery.data) {
      setUserState(meQuery.data.data);
      setIsInitializing(false);
    } else if (meQuery.isError) {
      tokenStorage.clear();
      setUserState(null);
      setIsInitializing(false);
    }
  }, [meQuery.data, meQuery.isError]);

  useEffect(() => {
    function handleStorage(event: StorageEvent) {
      if (event.key === null || event.key.includes("cal_killer")) {
        if (!tokenStorage.getAccessToken()) {
          setUserState(null);
        }
      }
    }
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const login = useCallback(
    (accessToken: string, refreshToken: string, nextUser: User) => {
      tokenStorage.setTokens(accessToken, refreshToken);
      setUserState(nextUser);
    },
    [],
  );

  const logout = useCallback(() => {
    tokenStorage.clear();
    setUserState(null);
  }, []);

  const setUser = useCallback((nextUser: User) => {
    setUserState(nextUser);
  }, []);

  const value: AuthContextValue = {
    user,
    isLoading: isInitializing,
    isAuthenticated: user !== null,
    login,
    logout,
    setUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
