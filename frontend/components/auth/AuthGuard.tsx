"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./AuthProvider";

interface AuthGuardProps {
  children: React.ReactNode;
  requiredRole?: "customer" | "admin";
}

/**
 * Reusable layout wrapper that guards pages from unauthorized users.
 * Automatically handles loading states and client-side redirection checks.
 */
export function AuthGuard({ children, requiredRole }: AuthGuardProps) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      if (!user) {
        // Not authenticated -> redirect to login
        router.push("/login");
      } else if (requiredRole && user.role !== requiredRole) {
        // Unauthorized role -> redirect to dashboard
        router.push("/dashboard");
      }
    }
  }, [user, loading, requiredRole, router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50 dark:bg-neutral-950">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
          <p className="text-sm font-semibold text-neutral-500 dark:text-neutral-400">
            Validating credentials...
          </p>
        </div>
      </div>
    );
  }

  // Hide page contents while redirecting in progress
  if (!user || (requiredRole && user.role !== requiredRole)) {
    return null;
  }

  return <>{children}</>;
}
