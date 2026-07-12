"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import {
  getProfile,
  loginUser,
  logoutUser,
  logoutAllSessions,
  refreshAccessToken,
  updateProfile,
  UserResponse
} from "../../services/auth";
import { normalizeError } from "../../lib/api-client";

interface AuthContextType {
  user: UserResponse | null;
  accessToken: string | null;
  loading: boolean;
  error: string | null;
  login: (credentials: Record<string, string>) => Promise<void>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  updateUser: (payload: { full_name?: string; preferred_language?: string }) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = async (token: string) => {
    try {
      const userData = await getProfile(token);
      setUser(userData);
      setError(null);
    } catch (err) {
      const normalized = normalizeError(err);
      setError(normalized.message);
      // Clean up in-memory tokens on profiles fetch failure
      setAccessToken(null);
      setUser(null);
    }
  };

  useEffect(() => {
    const restoreSession = async () => {
      try {
        const data = await refreshAccessToken();
        setAccessToken(data.access_token);
        const userData = await getProfile(data.access_token);
        setUser(userData);
        setError(null);
      } catch {
        // Silently catch refresh failures on startup (i.e. user is not logged in)
        setAccessToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    restoreSession();
  }, []);

  const login = async (credentials: Record<string, string>) => {
    setError(null);
    setLoading(true);
    try {
      const data = await loginUser(credentials);
      setAccessToken(data.access_token);
      await fetchProfile(data.access_token);
    } catch (err) {
      const normalized = normalizeError(err);
      setError(normalized.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setError(null);
    if (accessToken) {
      try {
        await logoutUser(accessToken);
      } catch (err) {
        console.error("Error during session logout:", err);
      }
    }
    setAccessToken(null);
    setUser(null);
  };

  const logoutAll = async () => {
    setError(null);
    if (accessToken) {
      try {
        await logoutAllSessions(accessToken);
      } catch (err) {
        console.error("Error during all device logout:", err);
      }
    }
    setAccessToken(null);
    setUser(null);
  };

  const updateUser = async (payload: { full_name?: string; preferred_language?: string }) => {
    setError(null);
    if (!accessToken) return;
    try {
      const updated = await updateProfile(accessToken, payload);
      setUser(updated);
    } catch (err) {
      const normalized = normalizeError(err);
      setError(normalized.message);
      throw err;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        loading,
        error,
        login,
        logout,
        logoutAll,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
