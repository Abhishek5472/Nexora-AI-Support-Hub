"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { registerUser } from "../../../services/auth";
import { normalizeError } from "../../../lib/api-client";
import { Card } from "../../../components/ui/Card";
import { Header } from "../../../components/layout/Header";
import { Footer } from "../../../components/layout/Footer";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [language, setLanguage] = useState("en");
  const [showPassword, setShowPassword] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const router = useRouter();

  // Password requirements validation calculated on the fly
  const checks = {
    length: password.length >= 8 && password.length <= 128,
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    digit: /\d/.test(password),
    special: /[!@#$%^&*(),.?\":{}|<>]/.test(password),
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !fullName || !password) {
      setError("All fields are required.");
      return;
    }

    // Verify all password requirements are met
    if (!Object.values(checks).every(Boolean)) {
      setError("Please satisfy all password security requirements.");
      return;
    }

    setFormLoading(true);
    try {
      await registerUser({
        email,
        full_name: fullName,
        password,
        preferred_language: language,
      });
      setSuccess(true);
      setTimeout(() => {
        router.push("/login");
      }, 2500);
    } catch (err) {
      setError(normalizeError(err).message);
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
              <h2 className="text-2xl font-bold">Create Account</h2>
              <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-2">
                Register as a customer with Nexora Technologies
              </p>
            </div>

            {success ? (
              <div className="text-center py-6">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-950/30 dark:text-emerald-450 mb-4">
                  ✓
                </div>
                <h3 className="text-lg font-bold text-neutral-800 dark:text-neutral-100">Registration Successful</h3>
                <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-2">
                  Redirecting you to the login page...
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold mb-1">Full Name</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full rounded-xl border border-neutral-350 bg-transparent px-4 py-2.5 text-sm outline-none focus:border-indigo-500 dark:border-neutral-800 dark:focus:border-indigo-500"
                    placeholder="John Doe"
                    disabled={formLoading}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-1">Email Address</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full rounded-xl border border-neutral-350 bg-transparent px-4 py-2.5 text-sm outline-none focus:border-indigo-500 dark:border-neutral-800 dark:focus:border-indigo-500"
                    placeholder="name@company.com"
                    disabled={formLoading}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-1">Preferred Language</label>
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

                <div>
                  <label className="block text-sm font-semibold mb-1">Password</label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full rounded-xl border border-neutral-350 bg-transparent px-4 py-2.5 text-sm outline-none focus:border-indigo-500 dark:border-neutral-800 dark:focus:border-indigo-500"
                      placeholder="••••••••"
                      disabled={formLoading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-3 text-xs font-semibold text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200"
                    >
                      {showPassword ? "Hide" : "Show"}
                    </button>
                  </div>
                </div>

                {/* Password Strength Checklist */}
                <div className="rounded-xl border border-neutral-200 dark:border-neutral-800/80 bg-neutral-50/50 p-3 text-xs space-y-1.5 dark:bg-neutral-900/20">
                  <p className="font-semibold text-neutral-500 dark:text-neutral-400 mb-1">Password requirements:</p>
                  <div className="flex items-center gap-2">
                    <span className={checks.length ? "text-emerald-500" : "text-neutral-400"}>
                      {checks.length ? "✓" : "○"}
                    </span>
                    <span>8-128 characters</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={checks.upper ? "text-emerald-500" : "text-neutral-400"}>
                      {checks.upper ? "✓" : "○"}
                    </span>
                    <span>At least one uppercase letter (A-Z)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={checks.lower ? "text-emerald-500" : "text-neutral-400"}>
                      {checks.lower ? "✓" : "○"}
                    </span>
                    <span>At least one lowercase letter (a-z)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={checks.digit ? "text-emerald-500" : "text-neutral-400"}>
                      {checks.digit ? "✓" : "○"}
                    </span>
                    <span>At least one digit (0-9)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={checks.special ? "text-emerald-500" : "text-neutral-400"}>
                      {checks.special ? "✓" : "○"}
                    </span>
                    <span>At least one special character (!@#$%^&*)</span>
                  </div>
                </div>

                {error && (
                  <div className="rounded-xl border border-rose-100 bg-rose-50/50 p-3 text-xs text-rose-600 dark:border-rose-950/20 dark:bg-rose-950/10 dark:text-rose-400">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={formLoading}
                  className="w-full rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 py-3 text-sm font-bold text-white shadow-md shadow-indigo-500/20 hover:from-indigo-600 hover:to-violet-750 active:scale-98 transition-all disabled:opacity-50"
                >
                  {formLoading ? "Creating account..." : "Register"}
                </button>
              </form>
            )}

            {!success && (
              <div className="text-center mt-6">
                <p className="text-xs text-neutral-500">
                  Already have an account?{" "}
                  <Link href="/login" className="font-semibold text-indigo-500 hover:underline">
                    Sign in here
                  </Link>
                </p>
              </div>
            )}
          </Card>
        </div>
      </main>
      <Footer />
    </div>
  );
}
