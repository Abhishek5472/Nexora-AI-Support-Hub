import { apiClient } from "../lib/api-client";

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  role: string;
  preferred_language: string;
  is_active: boolean;
  is_email_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

const authHeaders = (accessToken: string) => ({
  headers: {
    Authorization: `Bearer ${accessToken}`,
  },
});

/**
 * Registers a new user. Default role is customer.
 */
export async function registerUser(payload: Record<string, string>): Promise<UserResponse> {
  const response = await apiClient.post<UserResponse>("/auth/register", payload);
  return response.data;
}

/**
 * Logins in user, returns access token, and sets the HTTP-only refresh cookie.
 */
export async function loginUser(payload: Record<string, string>): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/login", payload);
  return response.data;
}

/**
 * Silent token refresh using the HTTP-only cookie. Rotates session and returns new access token.
 */
export async function refreshAccessToken(): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/refresh");
  return response.data;
}

/**
 * Logs out user from current session (clears cookies and revokes session doc).
 */
export async function logoutUser(accessToken: string): Promise<{ message: string }> {
  const response = await apiClient.post<{ message: string }>(
    "/auth/logout",
    {},
    authHeaders(accessToken)
  );
  return response.data;
}

/**
 * Logs out user from all active sessions (clears cookies and revokes all user sessions).
 */
export async function logoutAllSessions(accessToken: string): Promise<{ message: string }> {
  const response = await apiClient.post<{ message: string }>(
    "/auth/logout-all",
    {},
    authHeaders(accessToken)
  );
  return response.data;
}

/**
 * Fetches the user profile details using the memory-stored access token.
 */
export async function getProfile(accessToken: string): Promise<UserResponse> {
  const response = await apiClient.get<UserResponse>(
    "/auth/me",
    authHeaders(accessToken)
  );
  return response.data;
}

/**
 * Updates user profile settings (name and preferred language).
 */
export async function updateProfile(
  accessToken: string,
  payload: { full_name?: string; preferred_language?: string }
): Promise<UserResponse> {
  const response = await apiClient.patch<UserResponse>(
    "/users/me",
    payload,
    authHeaders(accessToken)
  );
  return response.data;
}

/**
 * Verifies role authorization for admins.
 */
export async function verifyAdmin(accessToken: string): Promise<{ status: string; role: string }> {
  const response = await apiClient.get<{ status: string; role: string }>(
    "/admin/verify",
    authHeaders(accessToken)
  );
  return response.data;
}
