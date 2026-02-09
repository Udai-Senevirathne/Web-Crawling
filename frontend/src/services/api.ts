/// <reference types="vite/client" />

// Use relative path for Vite proxy, or full URL if env var is set
const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || '/api';

export interface ChatResponse {
  response: string;
  sources: Array<{ url: string; title: string }>;
  session_id: string;
  context_used: boolean;
  timestamp: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface IngestionRequest {
  url: string;
  max_pages?: number;
  max_depth?: number;
  reset?: boolean;
}

export interface IngestionResponse {
  job_id: string;
  status: string;
  message: string;
  url: string;
  timestamp: string;
}

export interface IngestionStatus {
  job_id: string;
  status: string;
  url: string;
  progress: Record<string, any>;
  started_at?: string;
  completed_at?: string;
  error?: string;
}

export async function sendMessage(
  message: string,
  sessionId?: string,
  conversationHistory?: ChatMessage[]
): Promise<ChatResponse> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      message,
      session_id: sessionId,
      conversation_history: conversationHistory,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to send message');
  }

  return response.json();
}

export async function startIngestion(data: IngestionRequest): Promise<IngestionResponse> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/ingest`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Ingestion failed' }));
    throw new Error(err.detail || 'Ingestion request failed');
  }

  return response.json();
}

export async function getIngestionStatus(jobId: string): Promise<IngestionStatus> {
  const headers: Record<string, string> = {};
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/ingest/${jobId}`, { headers });
  if (!response.ok) {
    throw new Error(`Failed to get status: ${response.statusText}`);
  }
  return response.json();
}

export async function getStats() {
  const response = await fetch(`${API_BASE_URL}/chat/stats`);
  if (!response.ok) {
    throw new Error('Failed to get stats');
  }
  return response.json();
}

export async function listIngestionJobs() {
  const response = await fetch(`${API_BASE_URL}/ingest`);
  if (!response.ok) {
    throw new Error('Failed to list jobs');
  }
  return response.json();
}

export const deleteIngestionJob = async (jobId: string) => {
  const headers: Record<string, string> = {};
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/ingest/${jobId}`, {
    method: 'DELETE',
    headers,
  });
  if (!response.ok) {
    throw new Error('Failed to delete job');
  }
};

// Chat History & Settings
export async function getChatSessions() {
  const response = await fetch(`${API_BASE_URL}/chat/sessions`);
  if (!response.ok) throw new Error('Failed to fetch sessions');
  return response.json();
}

export async function getChatSession(sessionId: string) {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`);
  if (!response.ok) throw new Error('Failed to fetch session');
  return response.json();
}

export async function deleteChatSession(sessionId: string) {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
    method: 'DELETE'
  });
  if (!response.ok) throw new Error('Failed to delete session');
}

export async function getChatSettings() {
  const response = await fetch(`${API_BASE_URL}/chat/settings`);
  if (!response.ok) throw new Error('Failed to fetch settings');
  return response.json();
}

export async function updateChatSettings(systemPrompt: string) {
  const response = await fetch(`${API_BASE_URL}/chat/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ system_prompt: systemPrompt })
  });
  if (!response.ok) throw new Error('Failed to update settings');
  return response.json();
}

export async function resetDatabase() {
  const response = await fetch(`${API_BASE_URL}/ingest/reset`, { method: 'POST' });
  if (!response.ok) throw new Error('Failed to reset database');
  return response.json();
}
