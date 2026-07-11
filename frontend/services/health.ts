import { apiClient } from "../lib/api-client";

export interface GeneralHealthResponse {
  status: string;
  service: string;
  environment: string;
  version: string;
}

export interface DatabaseHealthResponse {
  status: string;
}

/**
 * Fetches the general backend health status.
 */
export async function getGeneralHealth(): Promise<GeneralHealthResponse> {
  const response = await apiClient.get<GeneralHealthResponse>("/api/v1/health");
  return response.data;
}

/**
 * Fetches the backend's database connection status.
 */
export async function getDatabaseHealth(): Promise<DatabaseHealthResponse> {
  const response = await apiClient.get<DatabaseHealthResponse>("/api/v1/health/database");
  return response.data;
}
