"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { fetchAPI } from "@/lib/api";

type User = {
  id: number;
  email: string;
  username: string;
  created_at: string;
};

type AuthContextType = {
  user: User | null;
  loading: boolean;
  login: (token: string) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem("token");
      if (token) {
        try {
          const userData = await fetchAPI("/auth/me");
          setUser(userData);
        } catch (error) {
          console.error("Auth init failed:", error);
          localStorage.removeItem("token");
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  const login = (token: string) => {
    localStorage.setItem("token", token);
    fetchAPI("/auth/me").then(setUser).catch(console.error);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
