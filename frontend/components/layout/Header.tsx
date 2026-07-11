import React from "react";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-neutral-200 bg-white/80 backdrop-blur-md dark:border-neutral-800 dark:bg-neutral-950/80">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 font-bold text-white shadow-md shadow-indigo-500/20">
            N
          </div>
          <div>
            <span className="text-lg font-bold tracking-tight text-neutral-900 dark:text-white">
              Nexora <span className="bg-gradient-to-r from-indigo-500 to-violet-600 bg-clip-text text-transparent font-extrabold">AI</span>
            </span>
            <span className="ml-1 text-xs font-semibold uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
              Support Hub
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="inline-flex items-center rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700 ring-1 ring-inset ring-indigo-700/10 dark:bg-indigo-950/30 dark:text-indigo-400 dark:ring-indigo-400/20">
            Phase 1 Foundation
          </span>
        </div>
      </div>
    </header>
  );
}
