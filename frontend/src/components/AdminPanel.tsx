import React, { useState, useEffect, useRef } from 'react';
import { startIngestion, getIngestionStatus, getStats, listIngestionJobs, deleteIngestionJob, uploadFiles, IngestionStatus } from '../services/api';
import './AdminPanel.css';

interface Stats {
  total_documents: number;
  model: string;
}

interface Job {
  job_id: string;
  url: string;
  status: string;
  started_at?: string;
}

export const AdminPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'url' | 'files'>('url');
  const [url, setUrl] = useState('');
  const [maxPages, setMaxPages] = useState(25);
  const [maxDepth, setMaxDepth] = useState(2);
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentJob, setCurrentJob] = useState<IngestionStatus | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (currentJob && ['pending', 'running'].includes(currentJob.status)) {
      const interval = setInterval(async () => {
        try {
          const status = await getIngestionStatus(currentJob.job_id);
          setCurrentJob(status);
          if (['completed', 'failed'].includes(status.status)) {
            clearInterval(interval);
            loadData();
            setMessage({
              type: status.status === 'completed' ? 'success' : 'error',
              text: status.status === 'completed'
                ? 'Processing completed successfully'
                : `Processing failed: ${status.error || 'Unknown error'}`
            });
          }
        } catch (err: any) {
          // If job not found (404), clear the current job and stop polling
          if (err?.message?.includes('404') || err?.message?.includes('not found')) {
            clearInterval(interval);
            setCurrentJob(null);
          }
          console.error('Status check failed:', err);
        }
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [currentJob]);

  const loadData = async () => {
    try {
      const [statsData, jobsData] = await Promise.all([
        getStats(),
        listIngestionJobs().catch(() => ({ jobs: [] }))
      ]);
      setStats(statsData.stats);
      setJobs(jobsData.jobs || []);
    } catch (err) {
      console.error('Failed to load data:', err);
    }
  };

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setMessage(null);

    try {
      const response = await startIngestion({
        url: url.trim(),
        max_pages: maxPages,
        max_depth: maxDepth,
      });

      setCurrentJob({
        job_id: response.job_id,
        status: 'running',
        url: response.url,
        progress: {},
      });
      setUrl('');
    } catch (err) {
      setMessage({ type: 'error', text: err instanceof Error ? err.message : 'Failed to start crawl' });
    } finally {
      setLoading(false);
    }
  };

  const handleFileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0) return;

    setLoading(true);
    setMessage(null);

    try {
      const data = await uploadFiles(files);
      setCurrentJob({
        job_id: data.job_id,
        status: 'running',
        url: `${files.length} file(s)`,
        progress: {},
      });
      setFiles([]);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      setMessage({ type: 'error', text: err instanceof Error ? err.message : 'Failed to upload files' });
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="crawl-view">
      {/* Header */}
      <header className="crawl-header">
        <div className="header-title">
          <h1>Content Ingestion</h1>
          <span className="header-subtitle">Add websites or documents to your knowledge base</span>
        </div>
      </header>

      <div className="crawl-content">
        {/* Stats */}
        <div className="stats-row">
          <div className="stat-card">
            <span className="stat-number">{stats?.total_documents || 0}</span>
            <span className="stat-text">Documents</span>
          </div>
          <div className="stat-card">
            <span className="stat-number">{jobs.length}</span>
            <span className="stat-text">Jobs</span>
          </div>
          <div className="stat-card">
            <span className="stat-number">{stats?.model?.split('-')[0] || '—'}</span>
            <span className="stat-text">Model</span>
          </div>
        </div>

        {/* Message */}
        {message && (
          <div className={`message-banner ${message.type}`}>
            {message.text}
            <button onClick={() => setMessage(null)}>×</button>
          </div>
        )}

        {/* Progress */}
        {currentJob && ['pending', 'running'].includes(currentJob.status) && (
          <div className="progress-card">
            <div className="progress-header">
              <span>Processing...</span>
              <span className="progress-status">{currentJob.status}</span>
            </div>
            <div className="progress-url">{currentJob.url}</div>
            <div className="progress-bar">
              <div className="progress-fill"></div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'url' ? 'active' : ''}`}
            onClick={() => setActiveTab('url')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            Website
          </button>
          <button
            className={`tab ${activeTab === 'files' ? 'active' : ''}`}
            onClick={() => setActiveTab('files')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            Documents
          </button>
        </div>

        {/* URL Form */}
        {activeTab === 'url' && (
          <form className="crawl-form" onSubmit={handleUrlSubmit}>
            <div className="form-group">
              <label>Website URL</label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com"
                required
                disabled={loading}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Max Pages</label>
                <input
                  type="number"
                  value={maxPages}
                  onChange={(e) => setMaxPages(Number(e.target.value))}
                  min={1}
                  max={200}
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label>Max Depth</label>
                <input
                  type="number"
                  value={maxDepth}
                  onChange={(e) => setMaxDepth(Number(e.target.value))}
                  min={1}
                  max={5}
                  disabled={loading}
                />
              </div>
            </div>

            <button type="submit" className="submit-btn" disabled={loading || !url.trim()}>
              {loading ? 'Starting...' : 'Crawl Website'}
            </button>
          </form>
        )}

        {/* Files Form */}
        {activeTab === 'files' && (
          <form className="crawl-form" onSubmit={handleFileSubmit}>
            <div className="form-group">
              <label>Upload Documents</label>
              <div
                className="file-dropzone"
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.txt,.md,.doc,.docx"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                />
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                <span>Click to upload or drag files here</span>
                <span className="file-hint">PDF, TXT, MD, DOC, DOCX</span>
              </div>
            </div>

            {files.length > 0 && (
              <div className="file-list">
                {files.map((file, index) => (
                  <div key={index} className="file-item">
                    <div className="file-info">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                      </svg>
                      <div>
                        <span className="file-name">{file.name}</span>
                        <span className="file-size">{formatFileSize(file.size)}</span>
                      </div>
                    </div>
                    <button type="button" className="file-remove" onClick={() => removeFile(index)}>
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}

            <button type="submit" className="submit-btn" disabled={loading || files.length === 0}>
              {loading ? 'Uploading...' : `Process ${files.length} File${files.length !== 1 ? 's' : ''}`}
            </button>
          </form>
        )}


        {/* History */}
        {jobs.length > 0 && (
          <div className="history-section">
            <h3>Recent Jobs</h3>
            <div className="history-list">
              {jobs.slice(0, 10).map((job) => (
                <div key={job.job_id} className="history-item">
                  <div className="history-info">
                    <span className="history-url">{job.url || 'File upload'}</span>
                    <span className="history-time">
                      {job.started_at ? new Date(job.started_at).toLocaleString() : '—'}
                    </span>
                  </div>
                  <div className="history-actions">
                    <span className={`status-badge ${job.status}`}>{job.status}</span>
                    <button
                      className="delete-btn"
                      onClick={async () => {
                        if (confirm('Are you sure you want to delete this content?')) {
                          try {
                            await deleteIngestionJob(job.job_id);
                            setJobs(jobs.filter(j => j.job_id !== job.job_id));
                            // Refresh stats
                            getStats().then(s => setStats(s.stats));
                          } catch (err) {
                            alert('Failed to delete job');
                          }
                        }
                      }}
                      title="Delete content"
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
