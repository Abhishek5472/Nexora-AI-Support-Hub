import axios, { AxiosError } from "axios";

// Environment-based API base URL check; falls back to localhost if not specified
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export interface ApiError {
  code: string;
  message: string;
  requestId?: string;
  status: number;
}

// In-memory access token tracking to prevent stale closures
let currentAccessToken: string | null = null;
let tokenRefreshedCallback: ((token: string | null) => void) | null = null;

export function setAccessTokenTracker(token: string | null) {
  currentAccessToken = token;
}

export function getAccessTokenTracker(): string | null {
  return currentAccessToken;
}

export function setTokenRefreshedCallback(callback: (token: string | null) => void) {
  tokenRefreshedCallback = callback;
}

export function triggerTokenRefreshed(token: string | null) {
  if (tokenRefreshedCallback) {
    tokenRefreshedCallback(token);
  }
}

/**
 * Centralized Axios instance configured for communications with the FastAPI backend.
 * withCredentials: true ensures HTTP-only cookies (refresh tokens) are sent automatically.
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Axios Request Interceptor: Inject the latest tracked token dynamically
apiClient.interceptors.request.use(
  (config) => {
    if (currentAccessToken && !config.headers["Authorization"]) {
      config.headers["Authorization"] = `Bearer ${currentAccessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Axios Response Interceptor: Intercept 401s, refresh token silently, and retry
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Check if error is a 401, not already retried, and not on auth endpoints
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/auth/refresh") &&
      !originalRequest.url?.includes("/auth/login")
    ) {
      originalRequest._retry = true;
      try {
        // Run direct refresh request avoiding instance interceptors loop
        const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {}, { withCredentials: true });
        const newToken = res.data.access_token;
        
        // Update both in-memory tracker and notify the AuthProvider
        setAccessTokenTracker(newToken);
        triggerTokenRefreshed(newToken);
        
        // Retry failed request with new token
        originalRequest.headers["Authorization"] = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshErr) {
        // Session expired, clear tokens
        setAccessTokenTracker(null);
        triggerTokenRefreshed(null);
        return Promise.reject(refreshErr);
      }
    }
    return Promise.reject(error);
  }
);

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
