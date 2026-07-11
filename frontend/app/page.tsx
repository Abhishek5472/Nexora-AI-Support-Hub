import React from "react";
import { Header } from "../components/layout/Header";
import { Footer } from "../components/layout/Footer";
import { Card } from "../components/ui/Card";
import { BackendHealthIndicator } from "../components/common/BackendHealthIndicator";

export default function Home() {
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
            {/* Frontend Status Card */}
            <Card>
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-neutral-800 dark:text-neutral-100">
                  Frontend Foundation
                </h2>
                <div className="flex items-center gap-1.5">
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-450 opacity-75"></span>
                    <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
                  </span>
                  <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">
                    Operational
                  </span>
                </div>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-neutral-600 dark:text-neutral-400">
                The Next.js frontend foundation is operational. Built with React, TypeScript, Tailwind CSS, App Router, and ESLint, it provides a premium foundation with a centralized Axios API client ready for subsequent service layers.
              </p>
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
