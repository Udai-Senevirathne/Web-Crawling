import React, { useState, useEffect } from 'react';
import { getChatSettings, updateChatSettings, resetDatabase } from '../services/api';
import './AdminPanel.css'; // Reuse existing styles

export const SettingsPanel: React.FC = () => {
    const [systemPrompt, setSystemPrompt] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            const settings = await getChatSettings();
            setSystemPrompt(settings.system_prompt || '');
        } catch (err) {
            console.error('Failed to load settings:', err);
        }
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setMessage(null);

        try {
            await updateChatSettings(systemPrompt);
            setMessage({ type: 'success', text: 'Settings updated successfully' });
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to update settings' });
        } finally {
            setLoading(false);
        }
    };

    const handleReset = async () => {
        if (!confirm('Are you absolutely sure you want to delete EVERYTHING? This cannot be undone.')) {
            return;
        }

        setLoading(true);
        setMessage(null);

        try {
            await resetDatabase();
            setMessage({ type: 'success', text: 'Database reset successfully' });
            localStorage.removeItem('session_id');
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to reset database' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="crawl-view">
            <header className="crawl-header">
                <div className="header-title">
                    <h1>AI Settings</h1>
                    <span className="header-subtitle">Customize your assistant's behavior</span>
                </div>
            </header>

            <div className="crawl-content">
                {message && (
                    <div className={`message-banner ${message.type}`}>
                        {message.text}
                        <button onClick={() => setMessage(null)}>×</button>
                    </div>
                )}

                <form className="crawl-form" onSubmit={handleSave}>
                    <div className="form-group">
                        <label>System Prompt</label>
                        <p className="form-hint">
                            Instructions for the AI assistant. Define its personality, tone, and constraints.
                        </p>
                        <textarea
                            value={systemPrompt}
                            onChange={(e) => setSystemPrompt(e.target.value)}
                            placeholder="You are a helpful assistant..."
                            rows={8}
                            className="settings-textarea"
                            disabled={loading}
                        />
                    </div>

                    <button type="submit" className="submit-btn" disabled={loading}>
                        {loading ? 'Saving...' : 'Save Settings'}
                    </button>
                </form>

                <div className="danger-zone">
                    <h2>Danger Zone</h2>
                    <div className="danger-item">
                        <div className="danger-info">
                            <h3>Reset Database</h3>
                            <p>Delete all indexed documents, chat history, and settings. This action cannot be undone.</p>
                        </div>
                        <button
                            className="danger-btn"
                            onClick={handleReset}
                            disabled={loading}
                        >
                            Reset Database
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
