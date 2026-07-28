import { useState, useEffect, type FormEvent } from 'react';
import { getUsers, createUser, updateUser, deleteUser } from '../services/api';
import type { User } from '../types';
import Spinner from '../components/Spinner';

interface UserForm {
  name: string;
  email: string;
  password: string;
  role: 'USER' | 'ADMIN';
}

const emptyForm: UserForm = { name: '', email: '', password: '', role: 'USER' };

interface FormErrors {
  name?: string;
  email?: string;
  password?: string;
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [form, setForm] = useState<UserForm>(emptyForm);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await getUsers();
      setUsers(data.content);
    } catch {
      // Mock data for dev
      setUsers([
        { id: '1', name: 'Alice Johnson', email: 'alice@example.com', role: 'ADMIN', active: true, createdAt: '2025-01-15T08:00:00Z' },
        { id: '2', name: 'Bob Smith', email: 'bob@example.com', role: 'USER', active: true, createdAt: '2025-02-20T10:30:00Z' },
        { id: '3', name: 'Charlie Brown', email: 'charlie@example.com', role: 'USER', active: false, createdAt: '2025-03-10T14:00:00Z' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  const openCreate = () => {
    setEditingUser(null);
    setForm(emptyForm);
    setFormErrors({});
    setShowModal(true);
  };

  const openEdit = (user: User) => {
    setEditingUser(user);
    setForm({ name: user.name, email: user.email, password: '', role: user.role });
    setFormErrors({});
    setShowModal(true);
  };

  const validate = (): boolean => {
    const errs: FormErrors = {};
    if (!form.name.trim()) errs.name = 'Name is required';
    if (!form.email.trim()) errs.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errs.email = 'Invalid email';
    if (!editingUser && !form.password) errs.password = 'Password is required';
    else if (!editingUser && form.password.length < 6) errs.password = 'Min 6 characters';
    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setSaving(true);
    setError('');
    try {
      if (editingUser) {
        const updated = await updateUser(editingUser.id, { name: form.name, email: form.email, role: form.role });
        setUsers((prev) => prev.map((u) => (u.id === editingUser.id ? updated : u)));
      } else {
        const created = await createUser(form);
        setUsers((prev) => [...prev, created]);
      }
      setShowModal(false);
    } catch {
      // Mock update for dev
      if (editingUser) {
        setUsers((prev) =>
          prev.map((u) => (u.id === editingUser.id ? { ...u, name: form.name, email: form.email, role: form.role } : u))
        );
      } else {
        const newUser: User = {
          id: Date.now().toString(),
          name: form.name,
          email: form.email,
          role: form.role,
          active: true,
          createdAt: new Date().toISOString(),
        };
        setUsers((prev) => [...prev, newUser]);
      }
      setShowModal(false);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this user?')) return;
    try {
      await deleteUser(id);
      setUsers((prev) => prev.filter((u) => u.id !== id));
    } catch {
      setUsers((prev) => prev.filter((u) => u.id !== id));
    }
  };

  if (loading) return (
    <div className="page-loading">
      <Spinner size="lg" ariaLabel="Loading users" />
      <span>Loading users...</span>
    </div>
  );

  return (
    <div className="page">
      <div className="page-header">
        <h1>Users</h1>
        <button className="btn btn-primary" onClick={openCreate}>+ New User</button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

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
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.name}</td>
                <td>{user.email}</td>
                <td><span className={`badge badge-${user.role === 'ADMIN' ? 'danger' : 'info'}`}>{user.role}</span></td>
                <td><span className={`badge badge-${user.active ? 'success' : 'muted'}`}>{user.active ? 'Active' : 'Inactive'}</span></td>
                <td>{new Date(user.createdAt).toLocaleDateString()}</td>
                <td className="actions-cell">
                  <button className="btn btn-sm btn-outline" onClick={() => openEdit(user)}>Edit</button>
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete(user.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{editingUser ? 'Edit User' : 'Create User'}</h2>
            <form onSubmit={handleSubmit} noValidate>
              <div className="form-group">
                <label>Name</label>
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={formErrors.name ? 'input-error' : ''} />
                {formErrors.name && <span className="field-error">{formErrors.name}</span>}
              </div>
              <div className="form-group">
                <label>Email</label>
                <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className={formErrors.email ? 'input-error' : ''} />
                {formErrors.email && <span className="field-error">{formErrors.email}</span>}
              </div>
              {!editingUser && (
                <div className="form-group">
                  <label>Password</label>
                  <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className={formErrors.password ? 'input-error' : ''} />
                  {formErrors.password && <span className="field-error">{formErrors.password}</span>}
                </div>
              )}
              <div className="form-group">
                <label>Role</label>
                <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as 'USER' | 'ADMIN' })}>
                  <option value="USER">User</option>
                  <option value="ADMIN">Admin</option>
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? (
                  <>
                    <Spinner size="sm" ariaLabel="Saving" />
                    <span>Saving...</span>
                  </>
                ) : (
                  'Save'
                )}
              </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
