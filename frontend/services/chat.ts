import axios from "axios";
import { 
  apiClient, 
  getAccessTokenTracker, 
  setAccessTokenTracker, 
  triggerTokenRefreshed 
} from "@/lib/api-client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export interface Citation {
  chunk_id: string;
  source_filename: string;
  document_title: string;
  page_start: number;
  page_end: number;
  similarity_score: number;
}

export interface Message {
  _id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  citations?: Citation[];
  is_interrupted?: boolean;
}

export interface Conversation {
  _id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

/**
 * Creates a new conversation session.
 */
export async function createConversation(title?: string): Promise<Conversation> {
  const res = await apiClient.post("/chat/conversations", { title });
  return res.data;
}

/**
 * Lists all conversations for the active user.
 */
export async function listConversations(): Promise<Conversation[]> {
  const res = await apiClient.get("/chat/conversations");
  return res.data;
}

/**
 * Fetches the metadata for a single conversation.
 */
export async function getConversation(id: string): Promise<Conversation> {
  const res = await apiClient.get(`/chat/conversations/${id}`);
  return res.data;
}

/**
 * Deletes a conversation and its messages.
 */
export async function deleteConversation(id: string): Promise<void> {
  await apiClient.delete(`/chat/conversations/${id}`);
}

/**
 * Clears message history for a conversation.
 */
export async function clearConversationMessages(id: string): Promise<void> {
  await apiClient.delete(`/chat/conversations/${id}/messages`);
}

/**
 * Fetches the message history logs of a conversation.
 */
export async function getConversationMessages(id: string): Promise<Message[]> {
  const res = await apiClient.get(`/chat/conversations/${id}/messages`);
  return res.data;
}

interface CustomRequestInit extends RequestInit {
  _retry?: boolean;
}

/**
 * Decodes the Server-Sent Events stream from the backend.
 * Integrates automatic token refresh retry logic for streaming fetch.
 */
async function readSSEStream(
  url: string,
  options: CustomRequestInit,
  onToken: (token: string) => void,
  onCitations: (citations: Citation[]) => void,
  onError: (err: string) => void,
  abortSignal?: AbortSignal
): Promise<void> {
  try {
    const response = await fetch(url, {
      ...options,
      signal: abortSignal
    });

    // Check if unauthorized, try token refresh once
    if (response.status === 401 && !options._retry) {
      options._retry = true;
      try {
        const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {}, { withCredentials: true });
        const newToken = res.data.access_token;
        
        // Sync new token trackers
        setAccessTokenTracker(newToken);
        triggerTokenRefreshed(newToken);
        
        // Update header and retry
        options.headers = {
          ...options.headers,
          "Authorization": `Bearer ${newToken}`
        };
        
        return await readSSEStream(url, options, onToken, onCitations, onError, abortSignal);
      } catch {
        setAccessTokenTracker(null);
        triggerTokenRefreshed(null);
        onError("Session has expired. Please login again.");
        return;
      }
    }

    if (!response.ok) {
      const errText = await response.text();
      let parsedErr = "Failed to generate AI response.";
      try {
        const json = JSON.parse(errText);
        parsedErr = json.detail || json.error?.message || parsedErr;
      } catch {}
      onError(parsedErr);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      onError("Streaming response body is unavailable.");
      return;
    }

    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      // Keep the last incomplete line in buffer
      buffer = lines.pop() || "";

      for (const line of lines) {
        const cleanLine = line.trim();
        if (!cleanLine.startsWith("data:")) continue;

        const rawJson = cleanLine.substring(5).trim();
        if (!rawJson) continue;

        try {
          const payload = JSON.parse(rawJson);
          if (payload.token) {
            onToken(payload.token);
          }
          if (payload.citations) {
            onCitations(payload.citations);
          }
          if (payload.error) {
            onError(payload.error);
          }
        } catch (e) {
          console.warn("Failed to parse SSE payload line:", rawJson, e);
        }
      }
    }
  } catch (error: unknown) {
    const err = error instanceof Error ? error : new Error(String(error));
    if (err.name === "AbortError") {
      console.info("Generation request aborted by user.");
    } else {
      onError(err.message || "An unexpected error occurred during streaming.");
    }
  }
}

/**
 * Submits a query, triggers FAISS retrieval, and streams back responses.
 */
export async function streamMessage(
  id: string,
  content: string,
  onToken: (token: string) => void,
  onCitations: (citations: Citation[]) => void,
  onError: (err: string) => void,
  abortSignal?: AbortSignal
): Promise<void> {
  const token = getAccessTokenTracker() || "";
  const url = `${API_BASE_URL}/chat/conversations/${id}/messages`;
  const options: CustomRequestInit = {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({ content })
  };

  await readSSEStream(url, options, onToken, onCitations, onError, abortSignal);
}

/**
 * Regenerates the last assistant message.
 */
export async function streamRegenerate(
  id: string,
  onToken: (token: string) => void,
  onCitations: (citations: Citation[]) => void,
  onError: (err: string) => void,
  abortSignal?: AbortSignal
): Promise<void> {
  const token = getAccessTokenTracker() || "";
  const url = `${API_BASE_URL}/chat/conversations/${id}/messages/regenerate`;
  const options: CustomRequestInit = {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`
    }
  };

  await readSSEStream(url, options, onToken, onCitations, onError, abortSignal);
}
