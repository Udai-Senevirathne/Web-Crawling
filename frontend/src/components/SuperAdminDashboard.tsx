import { useState, useEffect } from 'react';
import { 
  listClients, 
  createClient, 
  updateClient, 
  deleteClient, 
  getClientStats,
  Client, 
  ClientCreate 
} from '../services/api';
import './SuperAdminDashboard.css';

interface SuperAdminDashboardProps {
  onOpenClientAdmin?: (clientId: string) => void;
}

export function SuperAdminDashboard({ onOpenClientAdmin }: SuperAdminDashboardProps) {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [clientStats, setClientStats] = useState<any>(null);

  // Form state
  const [formData, setFormData] = useState<ClientCreate>({
    name: '',
    enl_id: '',
    status: 'active',
  });

  useEffect(() => {
    loadClients();
  }, []);

  const loadClients = async () => {
    try {
      setLoading(true);
      const data = await listClients();
      setClients(data);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load clients');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateClient = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createClient(formData);
      setShowCreateModal(false);
      setFormData({ name: '', enl_id: '', status: 'active' });
      loadClients();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create client');
    }
  };

  const handleDeleteClient = async (clientId: string, clientName: string) => {
    if (!confirm(`Are you sure you want to delete "${clientName}"? This will delete all associated users and data.`)) {
      return;
    }
    
    try {
      await deleteClient(clientId);
      loadClients();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete client');
    }
  };

  const handleViewStats = async (client: Client) => {
    try {
      const stats = await getClientStats(client.id);
      setClientStats(stats);
      setSelectedClient(client);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
    }
  };

  const handleToggleStatus = async (client: Client) => {
    try {
      const newStatus = client.status === 'active' ? 'suspended' : 'active';
      await updateClient(client.id, { status: newStatus });
      loadClients();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update status');
    }
  };

  return (
    <div className="super-admin-container">
      <div className="super-admin-header">
        <h1>Super Admin Dashboard</h1>
        <button className="create-client-btn" onClick={() => setShowCreateModal(true)}>
          + Create Client
        </button>
      </div>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      {loading ? (
        <div className="loading-spinner">Loading clients...</div>
      ) : (
        <div className="clients-grid">
          {clients.length === 0 ? (
            <div className="no-clients">
              <p>No clients yet. Create your first client to get started.</p>
            </div>
          ) : (
            clients.map(client => (
              <div
                key={client.id}
                className="client-card"
                onClick={() => onOpenClientAdmin ? onOpenClientAdmin(client.id) : undefined}
                style={{ cursor: onOpenClientAdmin ? 'pointer' : undefined }}
              >
                <div className="client-header">
                  <h3>{client.name}</h3>
                  <span className={`status-badge status-${client.status}`}>
                    {client.status}
                  </span>
                </div>
                <div className="client-info">
                  <p><strong>ENL ID:</strong> {client.enl_id}</p>
                  <p><strong>Documents:</strong> {client.document_count || 0}</p>
                  <p><strong>Created:</strong> {new Date(client.created_at).toLocaleDateString()}</p>
                </div>
                <div className="client-actions">
                  <button onClick={(e) => { e.stopPropagation(); handleViewStats(client); }}>📊 Stats</button>
                  <button onClick={(e) => { e.stopPropagation(); onOpenClientAdmin ? onOpenClientAdmin(client.id) : handleViewStats(client); }}>
                    🔧 Open
                  </button>
                  <button onClick={(e) => { e.stopPropagation(); handleToggleStatus(client); }}>
                    {client.status === 'active' ? '⏸️ Suspend' : '▶️ Activate'}
                  </button>
                  <button className="delete-btn" onClick={(e) => { e.stopPropagation(); handleDeleteClient(client.id, client.name); }}>
                    🗑️ Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Client</h2>
            <form onSubmit={handleCreateClient}>
              <div className="form-group">
                <label>Client Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Acme Corporation"
                  required
                />
              </div>
              <div className="form-group">
                <label>ENL ID (Unique Identifier)</label>
                <input
                  type="text"
                  value={formData.enl_id}
                  onChange={(e) => setFormData({ ...formData, enl_id: e.target.value })}
                  placeholder="e.g., acme_corp_123"
                  required
                />
              </div>
              <div className="form-group">
                <label>Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                >
                  <option value="active">Active</option>
                  <option value="suspended">Suspended</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit">Create Client</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedClient && clientStats && (
        <div className="modal-overlay" onClick={() => { setSelectedClient(null); setClientStats(null); }}>
          <div className="modal-content stats-modal" onClick={(e) => e.stopPropagation()}>
            <h2>{selectedClient.name} - Statistics</h2>
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-label">Users</div>
                <div className="stat-value">{clientStats.user_count}</div>
              </div>
              <div className="stat-item">
                <div className="stat-label">Chat Sessions</div>
                <div className="stat-value">{clientStats.chat_session_count}</div>
              </div>
              <div className="stat-item">
                <div className="stat-label">Documents</div>
                <div className="stat-value">{clientStats.document_count}</div>
              </div>
              <div className="stat-item">
                <div className="stat-label">Status</div>
                <div className="stat-value">{clientStats.status}</div>
              </div>
            </div>
            <div className="modal-actions">
              <button onClick={() => { setSelectedClient(null); setClientStats(null); }}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
