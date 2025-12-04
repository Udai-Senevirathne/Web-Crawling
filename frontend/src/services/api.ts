/// <reference types="vite/client" />

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api';

export interface ChatResponse {
  response: string;
  sources: Array<{url: string; title: string}>;
  session_id: string;
  context_used: boolean;
  timestamp: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export async function sendMessage(
  message: string,
  sessionId?: string,
  conversationHistory?: ChatMessage[]
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      session_id: sessionId || localStorage.getItem('session_id'),
      conversation_history: conversationHistory,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to send message');
  }

  const data = await response.json();

  // Store session ID
  if (data.session_id) {
    localStorage.setItem('session_id', data.session_id);
  }

  return data;
}

export async function getStats() {
  const response = await fetch(`${API_BASE_URL}/chat/stats`);

  if (!response.ok) {
    throw new Error('Failed to fetch stats');
  }

  return response.json();
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  return response.json();
}

