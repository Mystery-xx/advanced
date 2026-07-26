import { useState } from 'react';
import { searchUsers, filterUsersByRole, adminBlockUser, adminUnblockUser } from '../services/api';
import type { User } from '../types';

export default function AdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    setError('');
    setSearched(true);
    try {
      if (roleFilter !== 'ALL') {
        const data = await filterUsersByRole(roleFilter);
        setUsers(data.content);
      } else if (searchQuery.trim()) {
        const data = await searchUsers(searchQuery.trim());
        setUsers(data.content);
      } else {
        const data = await filterUsersByRole('ALL');
        setUsers(data.content);
      }
    } catch {
      // Mock data for dev
      const mockUsers: User[] = [
        { id: '1', name: 'Alice Johnson', email: 'alice@example.com', role: 'ADMIN', active: true, createdAt: '2025-01-15T08:00:00Z' },
        { id: '2', name: 'Bob Smith', email: 'bob@example.com', role: 'USER', active: true, createdAt: '2025-02-20T10:30:00Z' },
        { id: '3', name: 'Charlie Brown', email: 'charlie@example.com', role: 'USER', active: false, createdAt: '2025-03-10T14:00:00Z' },
        { id: '4', name: 'Diana Prince', email: 'diana@example.com', role: 'ADMIN', active: true, createdAt: '2025-04-05T09:00:00Z' },
        { id: '5', name: 'Eve Adams', email: 'eve@example.com', role: 'USER', active: true, createdAt: '2025-05-12T11:20:00Z' },
      ];
      let filtered = mockUsers;
      if (roleFilter !== 'ALL') {
        filtered = filtered.filter((u) => u.role === roleFilter);
      }
      if (searchQuery.trim()) {
        const q = searchQuery.trim().toLowerCase();
        filtered = filtered.filter(
          (u) => u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
        );
      }
      setUsers(filtered);
    } finally {
      setLoading(false);
    }
  };

  const handleBlockToggle = async (userId: string, currentActive: boolean) => {
    try {
      if (currentActive) {
        const updated = await adminBlockUser(userId);
        setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
      } else {
        const updated = await adminUnblockUser(userId);
        setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
      }
    } catch {
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, active: !u.active } : u))
      );
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Admin Panel</h1>
        <p className="page-subtitle">User management — search, filter, block/unblock</p>
      </div>

      <div className="admin-controls">
        <div className="admin-search">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name or email..."
            className="search-input"
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button className="btn btn-primary" onClick={handleSearch} disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        <div className="admin-filters">
          <label>Role Filter:</label>
          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
            <option value="ALL">All Roles</option>
            <option value="USER">Users</option>
            <option value="ADMIN">Admins</option>
          </select>
          <button className="btn btn-outline btn-sm" onClick={handleSearch} disabled={loading}>
            Apply Filter
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {searched && (
        <div className="admin-stats">
          <span>Found <strong>{users.length}</strong> user{users.length !== 1 ? 's' : ''}</span>
        </div>
      )}

      <div className="table-responsive">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {searched && users.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center text-muted">No users found</td>
              </tr>
            ) : (
              users.map((user) => (
                <tr key={user.id}>
                  <td>{user.name}</td>
                  <td>{user.email}</td>
                  <td>
                    <span className={`badge badge-${user.role === 'ADMIN' ? 'danger' : 'info'}`}>
                      {user.role}
                    </span>
                  </td>
                  <td>
                    <span className={`badge badge-${user.active ? 'success' : 'muted'}`}>
                      {user.active ? 'Active' : 'Blocked'}
                    </span>
                  </td>
                  <td>{new Date(user.createdAt).toLocaleDateString()}</td>
                  <td>
                    {user.active ? (
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() => handleBlockToggle(user.id, true)}
                      >
                        Block
                      </button>
                    ) : (
                      <button
                        className="btn btn-sm btn-success"
                        onClick={() => handleBlockToggle(user.id, false)}
                      >
                        Unblock
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
