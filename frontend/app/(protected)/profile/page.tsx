"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "../../../components/auth/AuthProvider";
import { AuthGuard } from "../../../components/auth/AuthGuard";
import { Card } from "../../../components/ui/Card";
import { Header } from "../../../components/layout/Header";
import { Footer } from "../../../components/layout/Footer";
import { normalizeError } from "../../../lib/api-client";

export default function ProfilePage() {
  return (
    <AuthGuard>
      <ProfileContent />
    </AuthGuard>
  );
}

function ProfileContent() {
  const { user, updateUser, logoutAll } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [language, setLanguage] = useState(user?.preferred_language || "en");
  const [formLoading, setFormLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMsg(null);
    setErrorMsg(null);
    setFormLoading(true);

    try {
      await updateUser({ full_name: fullName, preferred_language: language });
      setSuccessMsg("Profile updated successfully!");
    } catch (err) {
      setErrorMsg(normalizeError(err).message);
    } finally {
      setFormLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-neutral-50 dark:bg-neutral-950 text-neutral-900 dark:text-neutral-50 transition-colors duration-300">
      <Header />
      <main className="flex-1 px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl">
          {/* Back link */}
          <div className="mb-6">
            <Link href="/dashboard" className="text-xs font-semibold text-indigo-500 hover:underline">
              ← Back to Dashboard
            </Link>
          </div>

          <div className="space-y-6">
            <Card>
              <h2 className="text-xl font-bold mb-6">User Account Settings</h2>
              
              <form onSubmit={handleUpdate} className="space-y-4">
                {/* Read-only account info */}
                <div className="grid gap-4 sm:grid-cols-2 border-b border-neutral-100 dark:border-neutral-800/80 pb-4 mb-4 text-sm">
                  <div>
                    <span className="block text-xs text-neutral-450 dark:text-neutral-500 font-semibold uppercase tracking-wider">Email Address</span>
                    <span className="font-semibold">{user?.email}</span>
                  </div>
                  <div>
                    <span className="block text-xs text-neutral-450 dark:text-neutral-500 font-semibold uppercase tracking-wider">Account Role</span>
                    <span className="capitalize font-semibold">{user?.role}</span>
                  </div>
                  <div>
                    <span className="block text-xs text-neutral-450 dark:text-neutral-500 font-semibold uppercase tracking-wider">Account Status</span>
                    <span className="inline-flex items-center gap-1 mt-0.5 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold ring-1 ring-inset ring-emerald-700/10 dark:bg-emerald-950/20 dark:text-emerald-400">
                      Active
                    </span>
                  </div>
                </div>

                {/* Editable Fields */}
                <div>
                  <label className="block text-sm font-semibold mb-2">Full Name</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full rounded-xl border border-neutral-350 bg-transparent px-4 py-2.5 text-sm outline-none focus:border-indigo-500 dark:border-neutral-800 dark:focus:border-indigo-500"
                    disabled={formLoading}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Preferred Language</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full rounded-xl border border-neutral-350 bg-transparent px-4 py-2.5 text-sm outline-none focus:border-indigo-500 dark:border-neutral-800 dark:bg-neutral-900 dark:focus:border-indigo-500"
                    disabled={formLoading}
                  >
                    <option value="en" className="dark:bg-neutral-900">English</option>
                    <option value="hi" className="dark:bg-neutral-900">Hindi (हिन्दी)</option>
                    <option value="mr" className="dark:bg-neutral-900">Marathi (मराठी)</option>
                  </select>
                </div>

                {successMsg && (
                  <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-3 text-xs text-emerald-600 dark:border-emerald-950/20 dark:bg-emerald-950/10 dark:text-emerald-400">
                    {successMsg}
                  </div>
                )}

                {errorMsg && (
                  <div className="rounded-xl border border-rose-100 bg-rose-50/50 p-3 text-xs text-rose-600 dark:border-rose-950/20 dark:bg-rose-950/10 dark:text-rose-400">
                    {errorMsg}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={formLoading}
                  className="rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 text-sm font-semibold transition-all disabled:opacity-50"
                >
                  {formLoading ? "Saving..." : "Save Settings"}
                </button>
              </form>
            </Card>

            {/* Session Management */}
            <Card className="border border-rose-200/20 dark:border-rose-950/10">
              <h3 className="font-bold text-base text-rose-600 dark:text-rose-400 mb-1">Danger Zone</h3>
              <p className="text-xs text-neutral-500 mb-4">
                Revoke all active logins and refresh sessions across all your devices. You will be required to log in again.
              </p>
              <button
                onClick={logoutAll}
                className="rounded-xl border border-rose-250 bg-transparent hover:bg-rose-50 text-rose-650 dark:border-rose-950/30 dark:hover:bg-rose-950/10 px-4 py-2 text-xs font-bold transition-all"
              >
                Log Out of All Devices
              </button>
            </Card>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
