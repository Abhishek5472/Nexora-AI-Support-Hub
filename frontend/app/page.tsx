"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "../components/auth/AuthProvider";
import { Header } from "../components/layout/Header";
import { Footer } from "../components/layout/Footer";
import { Card } from "../components/ui/Card";
import { BackendHealthIndicator } from "../components/common/BackendHealthIndicator";

export default function Home() {
  const { user, loading } = useAuth();

  return (
    <div className="flex min-h-screen flex-col bg-neutral-50 text-neutral-900 transition-colors duration-300 dark:bg-neutral-950 dark:text-neutral-50">
      <Header />
      
      <main className="flex-1 px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl">
          {/* Brand Intro */}
          <div className="mb-10 text-center">
            <span className="inline-flex items-center rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700 ring-1 ring-inset ring-indigo-700/10 dark:bg-indigo-950/30 dark:text-indigo-400 dark:ring-indigo-400/20">
              Nexora Technologies
            </span>
            <h1 className="mt-4 text-4xl font-extrabold tracking-tight sm:text-5xl">
              Nexora AI Support Hub
            </h1>
            <p className="mt-3 text-lg text-neutral-500 dark:text-neutral-400 font-medium">
              Smart Technology. Smarter Support.
            </p>
          </div>

          <div className="space-y-6">
            {/* Phase 2 Access Card */}
            <Card>
              <h2 className="text-xl font-bold mb-3 text-neutral-800 dark:text-neutral-100">
                Phase 2 Portal Portal Access
              </h2>
              <p className="text-sm text-neutral-600 dark:text-neutral-400 leading-relaxed mb-6">
                Welcome to the customer support system. Phase 2 introduces MongoDB-backed secure session authentication, refresh token rotation, user profile updates, and role-based access control (RBAC).
              </p>

              {loading ? (
                <div className="flex items-center justify-center py-4">
                  <div className="h-6 w-6 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
                </div>
              ) : user ? (
                <div className="flex flex-col sm:flex-row gap-3">
                  <Link
                    href="/dashboard"
                    className="flex-1 text-center rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 py-3 text-sm font-bold text-white shadow-md shadow-indigo-500/20 hover:from-indigo-600 hover:to-violet-750 transition-all"
                  >
                    Go to Dashboard
                  </Link>
                </div>
              ) : (
                <div className="flex flex-col sm:flex-row gap-3">
                  <Link
                    href="/login"
                    className="flex-1 text-center rounded-xl bg-indigo-650 hover:bg-indigo-700 py-3 text-sm font-bold text-white shadow-md transition-all"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/register"
                    className="flex-1 text-center rounded-xl border border-neutral-300 bg-white hover:bg-neutral-50 py-3 text-sm font-bold text-neutral-700 transition-all dark:border-neutral-800 dark:bg-neutral-900/40 dark:text-neutral-300 dark:hover:bg-neutral-800"
                  >
                    Register
                  </Link>
                </div>
              )}
            </Card>

            {/* Health Check Card */}
            <Card>
              <BackendHealthIndicator />
            </Card>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
