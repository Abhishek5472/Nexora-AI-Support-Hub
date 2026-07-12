"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "../../../components/auth/AuthProvider";
import { AuthGuard } from "../../../components/auth/AuthGuard";
import { verifyAdmin } from "../../../services/auth";
import { Card } from "../../../components/ui/Card";
import { Header } from "../../../components/layout/Header";
import { Footer } from "../../../components/layout/Footer";

export default function AdminPage() {
  return (
    <AuthGuard requiredRole="admin">
      <AdminContent />
    </AuthGuard>
  );
}

function AdminContent() {
  const { accessToken } = useAuth();
  const [adminVerified, setAdminVerified] = useState<boolean | null>(null);
  const [adminData, setAdminData] = useState<{
    status: string;
    role: string;
    email?: string;
    full_name?: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAdmin = async () => {
      if (!accessToken) return;
      try {
        const data = await verifyAdmin(accessToken);
        setAdminVerified(true);
        setAdminData(data);
      } catch {
        setAdminVerified(false);
      } finally {
        setLoading(false);
      }
    };

    checkAdmin();
  }, [accessToken]);

  return (
    <div className="flex min-h-screen flex-col bg-neutral-50 dark:bg-neutral-950 text-neutral-900 dark:text-neutral-50 transition-colors duration-300">
      <Header />
      <main className="flex-1 px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl">
          {/* Back link */}
          <div className="mb-6">
            <Link href="/dashboard" className="text-xs font-semibold text-indigo-500 hover:underline">
              ← Back to Dashboard
            </Link>
          </div>

          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
                <p className="text-sm font-semibold text-neutral-500 dark:text-neutral-400">
                  Verifying administrative security...
                </p>
              </div>
            </div>
          ) : adminVerified ? (
            <div className="space-y-6">
              <div className="mb-8">
                <h1 className="text-3xl font-bold text-violet-600 dark:text-violet-400">Admin Control Panel</h1>
                <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
                  Secure administration interface verified by Role-Based Access Control
                </p>
              </div>

              <Card>
                <div className="flex items-center gap-2 border-b border-neutral-100 dark:border-neutral-800/85 pb-4 mb-4">
                  <span className="h-2 w-2 rounded-full bg-violet-500"></span>
                  <h2 className="text-lg font-bold">Administrative Access Verified</h2>
                </div>
                
                <p className="text-sm text-neutral-600 dark:text-neutral-400 leading-relaxed mb-4">
                  Welcome to the administration view, <span className="font-semibold">{adminData?.full_name}</span> ({adminData?.email}). Your session role is authenticated as <span className="font-semibold text-violet-500">admin</span>.
                </p>

                <div className="rounded-xl border border-violet-100 bg-violet-50/50 p-4 text-xs text-violet-855 dark:border-violet-950/20 dark:bg-violet-950/10 dark:text-violet-400 leading-relaxed">
                  <span className="font-bold">System Status:</span> Safe development environment active. In later phases, this panel will house agent system diagnostics, knowledge base synchronization controls, prompt updates, and user session audits.
                </div>
              </Card>
            </div>
          ) : (
            <Card className="border border-rose-200/20 dark:border-rose-950/10">
              <div className="text-center py-6">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-100 text-rose-600 dark:bg-rose-950/30 dark:text-rose-450 mb-4">
                  !
                </div>
                <h3 className="text-lg font-bold text-neutral-850 dark:text-neutral-100">Access Denied</h3>
                <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-2 max-w-sm mx-auto">
                  Your account role does not possess the permissions required to view administrative configurations.
                </p>
              </div>
            </Card>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
