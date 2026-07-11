import React from "react";

export function Footer() {
  return (
    <footer className="w-full border-t border-neutral-200 bg-white py-6 dark:border-neutral-800 dark:bg-neutral-950">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 sm:flex-row sm:px-6 lg:px-8">
        <div className="text-center sm:text-left">
          <p className="text-sm text-neutral-500 dark:text-neutral-400">
            &copy; {new Date().getFullYear()} Nexora Technologies. All rights reserved.
          </p>
        </div>
        <div className="text-center sm:text-right">
          <p className="text-xs font-semibold uppercase tracking-widest text-neutral-400 dark:text-neutral-500">
            Smart Technology. Smarter Support.
          </p>
        </div>
      </div>
    </footer>
  );
}
