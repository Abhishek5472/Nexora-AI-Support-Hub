"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "../../../components/auth/AuthProvider";
import { AuthGuard } from "../../../components/auth/AuthGuard";
import { Card } from "../../../components/ui/Card";
import { Header } from "../../../components/layout/Header";
import { Footer } from "../../../components/layout/Footer";

export default function DashboardPage() {
  return (
    <AuthGuard>
      <DashboardContent />
    </AuthGuard>
  );
}

function DashboardContent() {
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen flex-col bg-neutral-50 dark:bg-neutral-950 text-neutral-900 dark:text-neutral-50 transition-colors duration-300">
      <Header />
      <main className="flex-1 px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl">
          {/* Greeting */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold">
              Hello, <span className="bg-gradient-to-r from-indigo-500 to-violet-600 bg-clip-text text-transparent font-extrabold">{user?.full_name}</span>
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
              Welcome to your Nexora Support Dashboard
            </p>
          </div>

          <div className="space-y-6">
            {/* Phase 2 Operational Banner */}
            <Card>
              <div className="flex items-center justify-between border-b border-neutral-100 dark:border-neutral-850 pb-4 mb-4">
                <h2 className="text-lg font-bold">Authentication & RBAC Operational</h2>
                <span className="inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 ring-1 ring-inset ring-emerald-700/10 dark:bg-emerald-950/30 dark:text-emerald-450">
                  Secure Session Active
                </span>
              </div>
              <p className="text-sm text-neutral-600 dark:text-neutral-400 leading-relaxed">
                Your customer profile session is secured using standard SHA-256 refresh-token rotation stored in MongoDB, and access tokens held securely in React memory. 
              </p>
              <div className="mt-4 rounded-xl border border-indigo-150 bg-indigo-50/40 p-4 text-xs text-indigo-700 dark:border-indigo-950/20 dark:bg-indigo-950/10 dark:text-indigo-400 leading-relaxed">
                <span className="font-bold">Note:</span> The intelligent customer support RAG chat pipeline is fully active. You can start a conversation grounded in our official company knowledge documents in English, Hindi, and Marathi.
              </div>
            </Card>

            {/* Quick Actions */}
            <div className="grid gap-4 sm:grid-cols-2">
              <Card className="flex flex-col justify-between">
                <div>
                  <h3 className="font-bold text-base mb-1">User Profile</h3>
                  <p className="text-xs text-neutral-500 mb-4">
                    Manage preferred language, name details, and device sessions.
                  </p>
                </div>
                <Link
                  href="/profile"
                  className="inline-flex items-center justify-center rounded-xl bg-neutral-200 hover:bg-neutral-355 dark:bg-neutral-900 dark:hover:bg-neutral-850 py-2.5 text-xs font-semibold tracking-wider transition-all"
                >
                  View Profile
                </Link>
              </Card>

              <Card className="flex flex-col justify-between border border-indigo-200 dark:border-indigo-950/30">
                <div>
                  <h3 className="font-bold text-base mb-1 text-indigo-650 dark:text-indigo-400">AI Support Chat</h3>
                  <p className="text-xs text-neutral-500 mb-4">
                    Ask support queries regarding setup, prices, warranty, shipping, and refunds.
                  </p>
                </div>
                <Link
                  href="/chat"
                  className="inline-flex items-center justify-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 py-2.5 text-xs font-semibold tracking-wider transition-all"
                >
                  Start AI Chat
                </Link>
              </Card>

              {user?.role === "admin" && (
                <Card className="flex flex-col justify-between border border-violet-200 dark:border-violet-950/30">
                  <div>
                    <h3 className="font-bold text-base mb-1 text-violet-600 dark:text-violet-400">Admin Control Panel</h3>
                    <p className="text-xs text-neutral-500 mb-4">
                      Access administrative verification configurations and audit controls.
                    </p>
                  </div>
                  <Link
                    href="/admin"
                    className="inline-flex items-center justify-center rounded-xl bg-violet-650 text-white hover:bg-violet-700 py-2.5 text-xs font-semibold tracking-wider transition-all"
                  >
                    Enter Admin Panel
                  </Link>
                </Card>
              )}
            </div>

            {/* Logout Link */}
            <div className="text-center pt-4">
              <button
                onClick={logout}
                className="text-xs font-semibold text-neutral-400 hover:text-rose-500 transition-all underline"
              >
                Log Out of Current Session
              </button>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
