import axios, { AxiosError } from "axios";

// Environment-based API base URL check; falls back to localhost if not specified
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface ApiError {
  code: string;
  message: string;
  requestId?: string;
  status: number;
}

/**
 * Centralized Axios instance configured for communications with the FastAPI backend.
 * withCredentials: true ensures HTTP-only cookies (refresh tokens) are sent automatically.
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 5000,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Normalizes all kinds of API errors (HTTP errors, timeouts, network failures, etc.)
 * into a single consistent client-side ApiError type.
 */
export function normalizeError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ error?: { code?: string; message?: string; request_id?: string } }>;
    const status = axiosError.response?.status || 500;

    // Check if FastAPI returned a structured custom exception handler error response
    if (axiosError.response?.data?.error) {
      const serverError = axiosError.response.data.error;
      return {
        code: serverError.code || "SERVER_ERROR",
        message: serverError.message || "An error occurred on the server.",
        requestId: serverError.request_id,
        status,
      };
    }

    // Check for timeout errors
    if (axiosError.code === "ECONNABORTED" || axiosError.message.includes("timeout")) {
      return {
        code: "TIMEOUT_ERROR",
        message: "The request timed out. The server might be busy or offline.",
        status: 408,
      };
    }

    // Check for network connectivity errors
    if (axiosError.code === "ERR_NETWORK" || !axiosError.response) {
      return {
        code: "NETWORK_ERROR",
        message: "Could not reach the backend server. Please verify it is running and accessible.",
        status: 503,
      };
    }

    return {
      code: axiosError.code || "HTTP_ERROR",
      message: axiosError.message || "An HTTP error occurred during the request.",
      status,
    };
  }

  // Handle generic runtime JavaScript errors
  return {
    code: "UNEXPECTED_ERROR",
    message: error instanceof Error ? error.message : "An unexpected error occurred.",
    status: 500,
  };
}
