import React, { useState, useEffect } from 'react';
import './AdminPanel.css';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api';

interface IngestionJob {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  url: string;
  started_at: string;
  completed_at?: string;
  error?: string;
}

interface Stats {
  total_documents: number;
  top_k: number;
  model: string;
  embedding_model: string;
}

export const AdminPanel: React.FC = () => {
  const [url, setUrl] = useState('');
  const [maxPages, setMaxPages] = useState(50);
  const [maxDepth, setMaxDepth] = useState(3);
  const [reset, setReset] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentJob, setCurrentJob] = useState<IngestionJob | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Fetch stats on mount
  useEffect(() => {
    fetchStats();
  }, []);

  // Poll job status when there's an active job
  useEffect(() => {
    if (currentJob && (currentJob.status === 'pending' || currentJob.status === 'running')) {
      const interval = setInterval(() => {
        checkJobStatus(currentJob.job_id);
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [currentJob]);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/stats`);
      if (response.ok) {
        const data = await response.json();
        // API returns { stats: {...}, timestamp: "..." }
        setStats(data.stats || data);
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const checkJobStatus = async (jobId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/ingest/${jobId}`);
      if (response.ok) {
        const data = await response.json();
        setCurrentJob(data);
        
        if (data.status === 'completed') {
          setSuccess('Content imported successfully! The knowledge base has been updated.');
          fetchStats(); // Refresh stats
        } else if (data.status === 'failed') {
          setError(`Import failed: ${data.error}`);
        }
      }
    } catch (err) {
      console.error('Failed to check job status:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/ingest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url.trim(),
          max_pages: maxPages,
          max_depth: maxDepth,
          reset: reset,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start ingestion');
      }

      const data = await response.json();
      setCurrentJob({
        job_id: data.job_id,
        status: 'pending',
        url: data.url,
        started_at: data.timestamp,
      });
      setSuccess('Import started successfully. Please wait while we process the content...');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start import');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#10b981';
      case 'running': return '#3b82f6';
      case 'pending': return '#f59e0b';
      case 'failed': return '#ef4444';
      default: return '#6b7280';
    }
  };

  return (
    <div className="admin-panel">
      <div className="admin-container">
        <header className="admin-header">
          <h1>Knowledge Base Management</h1>
          <p>Configure and manage your chatbot's content sources</p>
        </header>

        {/* Stats Card */}
        <div className="stats-card">
          <h2>System Overview</h2>
          {stats ? (
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-value">{stats.total_documents}</span>
                <span className="stat-label">Indexed Documents</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{stats.model?.replace('models/', '') || 'N/A'}</span>
                <span className="stat-label">Language Model</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{stats.embedding_model?.replace('models/', '') || 'N/A'}</span>
                <span className="stat-label">Embedding Model</span>
              </div>
            </div>
          ) : (
            <p className="loading-text">Loading system information...</p>
          )}
        </div>

        {/* Ingestion Form */}
        <div className="ingestion-card">
          <h2>Add Content Source</h2>
          <p>Enter a website URL to crawl and add its content to the knowledge base.</p>

          <form onSubmit={handleSubmit} className="ingestion-form">
            <div className="form-group">
              <label htmlFor="url">Website URL</label>
              <input
                type="url"
                id="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.example.com"
                required
                disabled={loading || (currentJob?.status === 'running')}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="maxPages">Page Limit</label>
                <input
                  type="number"
                  id="maxPages"
                  value={maxPages}
                  onChange={(e) => setMaxPages(parseInt(e.target.value) || 50)}
                  min={1}
                  max={500}
                  disabled={loading || (currentJob?.status === 'running')}
                />
              </div>

              <div className="form-group">
                <label htmlFor="maxDepth">Crawl Depth</label>
                <input
                  type="number"
                  id="maxDepth"
                  value={maxDepth}
                  onChange={(e) => setMaxDepth(parseInt(e.target.value) || 3)}
                  min={1}
                  max={10}
                  disabled={loading || (currentJob?.status === 'running')}
                />
              </div>
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={reset}
                  onChange={(e) => setReset(e.target.checked)}
                  disabled={loading || (currentJob?.status === 'running')}
                />
                Replace existing content (removes all previous data)
              </label>
            </div>

            <button
              type="submit"
              className="submit-btn"
              disabled={loading || !url.trim() || (currentJob?.status === 'running')}
            >
              {loading ? 'Initializing...' : currentJob?.status === 'running' ? 'Processing...' : 'Start Import'}
            </button>
          </form>

          {/* Status Messages */}
          {error && <div className="message error">{error}</div>}
          {success && <div className="message success">{success}</div>}

          {/* Job Status */}
          {currentJob && (
            <div className="job-status">
              <h3>Import Status</h3>
              <div className="job-details">
                <p><strong>Source:</strong> {currentJob.url}</p>
                <p>
                  <strong>Status:</strong>{' '}
                  <span style={{ color: getStatusColor(currentJob.status) }}>
                    {currentJob.status.charAt(0).toUpperCase() + currentJob.status.slice(1)}
                  </span>
                </p>
                <p><strong>Started:</strong> {new Date(currentJob.started_at).toLocaleString()}</p>
                {currentJob.completed_at && (
                  <p><strong>Completed:</strong> {new Date(currentJob.completed_at).toLocaleString()}</p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="instructions-card">
          <h2>Quick Guide</h2>
          <ol>
            <li>Enter the website URL you want to import content from</li>
            <li>Adjust the page limit and crawl depth as needed</li>
            <li>Click "Start Import" to begin processing</li>
            <li>Monitor the progress in the status section above</li>
            <li>Once complete, users can immediately start asking questions</li>
          </ol>
        </div>
      </div>
    </div>
  );
};
