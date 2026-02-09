import React, { useState, useEffect, useRef } from 'react';
import { sendMessage, getChatSessions, getChatSession, deleteChatSession, ChatMessage as ApiChatMessage, getStats } from '../services/api';
import './ClientChat.css';

interface Message extends ApiChatMessage {
  sources?: Array<{ url: string; title: string }>;
  id: string;
}

interface Session {
  session_id: string;
  last_message: string;
  updated_at: string;
  message_count: number;
}

interface ClientChatProps {
  resetTrigger?: number;
}

export const ClientChat: React.FC<ClientChatProps> = ({ resetTrigger }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [docCount, setDocCount] = useState(0);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (resetTrigger) {
      startNewChat();
    }
  }, [resetTrigger]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    getStats().then(data => setDocCount(data.stats?.total_documents || 0)).catch(() => { });
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await getChatSessions();
      setSessions(data.sessions || []);
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  };

  const loadSession = async (id: string) => {
    try {
      const data = await getChatSession(id);
      setSessionId(data.session_id);
      setMessages(data.messages.map((m: any) => ({
        ...m,
        id: Math.random().toString(36).substring(2, 9)
      })));
    } catch (err) {
      console.error('Failed to load session:', err);
    }
  };

  const deleteSession = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!confirm('Delete this conversation?')) return;

    try {
      await deleteChatSession(id);
      setSessions(prev => prev.filter(s => s.session_id !== id));
      if (sessionId === id) {
        startNewChat();
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const startNewChat = () => {
    setSessionId(undefined);
    setMessages([]);
    setInput('');
    inputRef.current?.focus();
  };

  const generateId = () => Math.random().toString(36).substring(2, 9);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = { role: 'user', content: input, id: generateId() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Optimistic update for session list
      if (!sessionId) {
        // We'll get a real session ID from the response
      }

      const history = messages.slice(-10).map(m => ({ role: m.role, content: m.content }));
      const response = await sendMessage(input, sessionId, history);

      setSessionId(response.session_id);

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.response,
        sources: response.sources,
        id: generateId()
      }]);

      // Refresh sessions list
      loadSessions();
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Unable to process your request. Please try again.',
        id: generateId()
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-layout">
      {/* History Sidebar */}
      <div className={`chat-history ${showHistory ? 'open' : 'closed'}`}>
        <div className="history-list">
          {sessions.map(session => (
            <div
              key={session.session_id}
              className={`history-item ${session.session_id === sessionId ? 'active' : ''}`}
              onClick={() => loadSession(session.session_id)}
            >
              <div className="history-text">
                <div className="history-title">{session.last_message}</div>
                <div className="history-date">
                  {new Date(session.updated_at).toLocaleDateString()}
                </div>
              </div>
              <button
                className="delete-history-btn"
                onClick={(e) => deleteSession(e, session.session_id)}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="chat-main">
        {/* Header */}
        <header className="chat-header">
          <button
            className="toggle-history-btn"
            onClick={() => setShowHistory(!showHistory)}
            title="Toggle Sidebar"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
              <line x1="9" y1="3" x2="9" y2="21" />
            </svg>
          </button>
          <div className="header-title">
            <h1>Knowledge Assistant</h1>
            <span className="header-subtitle">{docCount} documents indexed</span>
          </div>
        </header>

        {/* Messages */}
        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
              <h2>Start a conversation</h2>
              <p>Ask questions about your indexed content</p>
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`message ${msg.role}`}>
                <div className="message-content">
                  <p>{msg.content}</p>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="message-sources">
                      <span className="sources-label">Sources</span>
                      <div className="sources-list">
                        {msg.sources.slice(0, 3).map((source, i) => (
                          <a key={i} href={source.url} target="_blank" rel="noopener noreferrer">
                            {source.title || 'View source'}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="message assistant">
              <div className="message-content">
                <div className="typing">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="chat-input-container">
          <div className="chat-input-wrapper">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question..."
              rows={1}
              disabled={loading}
            />
            <button onClick={handleSend} disabled={loading || !input.trim()} className="send-btn">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
