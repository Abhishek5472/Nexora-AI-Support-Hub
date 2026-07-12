"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../../components/auth/AuthProvider";
import { Card } from "../../../components/ui/Card";
import { Header } from "../../../components/layout/Header";
import { Footer } from "../../../components/layout/Footer";

export default function LoginPage() {
  const { login, error } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (!email || !password) {
      setLocalError("Email and password are required.");
      return;
    }

    setFormLoading(true);
    try {
      await login({ email, password });
      router.push("/dashboard");
    } catch {
      // Error details are displayed via useAuth's global error state
    } finally {
      setFormLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-neutral-50 dark:bg-neutral-950 text-neutral-900 dark:text-neutral-50 transition-colors duration-300">
      <Header />
      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <Card>
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold">Welcome Back</h2>
              <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-2">
                Sign in to your Nexora account
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-semibold mb-2">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-neutral-350 bg-transparent px-4 py-3 text-sm outline-none focus:border-indigo-500 dark:border-neutral-800 dark:focus:border-indigo-500"
                  placeholder="name@company.com"
                  disabled={formLoading}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-xl border border-neutral-350 bg-transparent px-4 py-3 text-sm outline-none focus:border-indigo-500 dark:border-neutral-800 dark:focus:border-indigo-500"
                    placeholder="••••••••"
                    disabled={formLoading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3.5 text-xs font-semibold text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200"
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              {(localError || error) && (
                <div className="rounded-xl border border-rose-100 bg-rose-50/50 p-3 text-xs text-rose-600 dark:border-rose-950/20 dark:bg-rose-950/10 dark:text-rose-400">
                  {localError || error}
                </div>
              )}

              <button
                type="submit"
                disabled={formLoading}
                className="w-full rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 py-3 text-sm font-bold text-white shadow-md shadow-indigo-500/20 hover:from-indigo-600 hover:to-violet-750 active:scale-98 transition-all disabled:opacity-50"
              >
                {formLoading ? "Signing in..." : "Sign In"}
              </button>
            </form>

            <div className="text-center mt-6">
              <p className="text-xs text-neutral-500">
                Don&apos;t have an account?{" "}
                <Link href="/register" className="font-semibold text-indigo-500 hover:underline">
                  Register here
                </Link>
              </p>
            </div>
          </Card>
        </div>
      </main>
      <Footer />
    </div>
  );
}
