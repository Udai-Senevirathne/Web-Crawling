import React, { useState, useEffect, useRef } from 'react';
import { sendMessage, ChatMessage as ApiChatMessage } from '../services/api';
import './ClientChat.css';

interface Message extends ApiChatMessage {
  sources?: Array<{ url: string; title: string }>;
  timestamp?: string;
}

export const ClientChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Add welcome message on mount
  useEffect(() => {
    setMessages([
      {
        role: 'assistant',
        content:
          "Hello! Welcome to our support chat. I'm here to help answer any questions you may have. How can I assist you today?",
      },
    ]);
  }, []);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      // Prepare conversation history (last 10 messages)
      const history = messages.slice(-10).map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      const response = await sendMessage(input, undefined, history);

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        sources: response.sources,
        timestamp: response.timestamp,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Error sending message:', err);
      setError(err instanceof Error ? err.message : 'Failed to send message');

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            "I apologize for the inconvenience. We're experiencing a temporary issue. Please try again shortly.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="client-chat">
      <div className="chat-container">
        {/* Header */}
        <header className="chat-header">
          <div className="header-info">
            <div className="bot-avatar">💬</div>
            <div>
              <h1>Crawl Assistant</h1>
              <span className="status-indicator">
                <span className="status-dot"></span>
                Available
              </span>
            </div>
          </div>
        </header>

        {/* Error Banner */}
        {error && (
          <div className="error-banner">
            ⚠️ {error}
            <button onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {/* Messages */}
        <div className="messages-container">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-avatar">
                {msg.role === 'user' ? '👤' : '💬'}
              </div>
              <div className="message-bubble">
                <div className="message-text">{msg.content}</div>

                {/* Sources */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="message-sources">
                    <p className="sources-label">Related Resources:</p>
                    <div className="sources-list">
                      {msg.sources.map((source, i) => (
                        <a
                          key={i}
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="source-link"
                        >
                          {source.title || source.url}
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {loading && (
            <div className="message assistant">
              <div className="message-avatar">💬</div>
              <div className="message-bubble">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your question here..."
              disabled={loading}
              rows={1}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="send-button"
            >
              {loading ? (
                <span className="loading-spinner"></span>
              ) : (
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              )}
            </button>
          </div>
          <p className="input-hint">Press Enter to send</p>
        </div>
      </div>
    </div>
  );
};
