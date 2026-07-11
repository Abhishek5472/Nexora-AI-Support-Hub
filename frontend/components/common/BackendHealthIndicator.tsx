"use client";

import React, { useEffect, useState } from "react";
import { getGeneralHealth, getDatabaseHealth } from "../../services/health";
import { normalizeError } from "../../lib/api-client";

type ConnectionState = "checking" | "connected" | "unavailable";

export function BackendHealthIndicator() {
  const [generalState, setGeneralState] = useState<ConnectionState>("checking");
  const [dbState, setDbState] = useState<string>("checking");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [appDetails, setAppDetails] = useState<{ service: string; environment: string; version: string } | null>(null);

  const fetchHealth = async () => {
    setGeneralState("checking");
    setDbState("checking");
    setErrorMessage(null);
    try {
      const general = await getGeneralHealth();
      setAppDetails({
        service: general.service,
        environment: general.environment,
        version: general.version,
      });
      setGeneralState("connected");

      try {
        const db = await getDatabaseHealth();
        setDbState(db.status);
      } catch {
        setDbState("unavailable");
      }
    } catch (err) {
      setGeneralState("unavailable");
      setDbState("unavailable");
      const normalized = normalizeError(err);
      setErrorMessage(normalized.message);
    }
  };

  useEffect(() => {
    // Run the health check asynchronously to prevent synchronous setState within the effect
    const initialCheck = setTimeout(() => {
      fetchHealth();
    }, 0);

    // Poll every 10 seconds for real-time status updates
    const interval = setInterval(fetchHealth, 10000);

    return () => {
      clearTimeout(initialCheck);
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h3 className="text-lg font-bold text-neutral-800 dark:text-neutral-100">System Integration Status</h3>
        <button
          onClick={fetchHealth}
          className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-neutral-200 bg-white px-3 py-1.5 text-xs font-semibold text-neutral-700 shadow-sm transition-all hover:bg-neutral-50 active:bg-neutral-100 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:bg-neutral-800/80"
        >
          Check Connection
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* General API Health */}
        <div className="flex items-center gap-3 rounded-xl border border-neutral-200/60 bg-neutral-50/50 p-4 dark:border-neutral-800/60 dark:bg-neutral-900/40">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white shadow-sm dark:bg-neutral-800">
            {generalState === "connected" ? (
              <span className="relative flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-500"></span>
              </span>
            ) : generalState === "checking" ? (
              <span className="relative flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75"></span>
                <span className="relative inline-flex h-3 w-3 rounded-full bg-amber-500"></span>
              </span>
            ) : (
              <span className="relative flex h-3 w-3">
                <span className="relative inline-flex h-3 w-3 rounded-full bg-rose-500"></span>
              </span>
            )}
          </div>
          <div>
            <div className="text-xs font-medium text-neutral-400 dark:text-neutral-500">FastAPI API Health</div>
            <div className="text-sm font-semibold text-neutral-800 dark:text-neutral-200">
              {generalState === "connected"
                ? "Backend Connected"
                : generalState === "checking"
                ? "Checking backend connection..."
                : "Backend Unavailable"}
            </div>
          </div>
        </div>

        {/* Database Health */}
        <div className="flex items-center gap-3 rounded-xl border border-neutral-200/60 bg-neutral-50/50 p-4 dark:border-neutral-800/60 dark:bg-neutral-900/40">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white shadow-sm dark:bg-neutral-800">
            {dbState === "connected" ? (
              <span className="relative flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-500"></span>
              </span>
            ) : dbState === "checking" ? (
              <span className="relative flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75"></span>
                <span className="relative inline-flex h-3 w-3 rounded-full bg-amber-500"></span>
              </span>
            ) : dbState === "not_configured" ? (
              <span className="relative flex h-3 w-3">
                <span className="relative inline-flex h-3 w-3 rounded-full bg-neutral-400"></span>
              </span>
            ) : (
              <span className="relative flex h-3 w-3">
                <span className="relative inline-flex h-3 w-3 rounded-full bg-rose-500"></span>
              </span>
            )}
          </div>
          <div>
            <div className="text-xs font-medium text-neutral-400 dark:text-neutral-500">MongoDB Database</div>
            <div className="text-sm font-semibold text-neutral-800 dark:text-neutral-200 capitalize">
              {dbState === "connected"
                ? "Connected"
                : dbState === "checking"
                ? "Checking status..."
                : dbState === "not_configured"
                ? "Not Configured"
                : "Unavailable"}
            </div>
          </div>
        </div>
      </div>

      {/* Connection Info */}
      {generalState === "connected" && appDetails && (
        <div className="rounded-xl bg-neutral-50 p-4 text-xs text-neutral-600 dark:bg-neutral-900/30 dark:text-neutral-400">
          <div className="grid grid-cols-2 gap-y-1.5 sm:grid-cols-3">
            <div>
              <span className="font-semibold">Service:</span> {appDetails.service}
            </div>
            <div>
              <span className="font-semibold">Environment:</span> {appDetails.environment}
            </div>
            <div>
              <span className="font-semibold">Version:</span> {appDetails.version}
            </div>
          </div>
        </div>
      )}

      {errorMessage && (
        <div className="rounded-xl border border-rose-100 bg-rose-50/50 p-3 text-xs text-rose-600 dark:border-rose-950/20 dark:bg-rose-950/10 dark:text-rose-400">
          <p className="font-semibold">Connection Error Details:</p>
          <p className="mt-0.5">{errorMessage}</p>
        </div>
      )}
    </div>
  );
}
