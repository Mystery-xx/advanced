import { useState, useEffect, type FormEvent } from 'react';
import { getOrders, createOrder, updateOrderStatus } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import type { Order } from '../types';

const statusColors: Record<Order['status'], string> = {
  PENDING: 'warning',
  CONFIRMED: 'info',
  SHIPPED: 'primary',
  DELIVERED: 'success',
  CANCELLED: 'danger',
};

interface CreateForm {
  product: string;
  quantity: string;
  total: string;
}

interface FormErrors {
  product?: string;
  quantity?: string;
  total?: string;
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<CreateForm>({ product: '', quantity: '1', total: '' });
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [saving, setSaving] = useState(false);
  const { user } = useAuth();

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const data = await getOrders();
      setOrders(data.content);
    } catch {
      setOrders([
        { id: 'ORD-001', userId: user?.id || '1', product: 'Widget A', quantity: 2, status: 'DELIVERED', total: 49.99, createdAt: '2025-06-01T10:00:00Z' },
        { id: 'ORD-002', userId: user?.id || '1', product: 'Gadget B', quantity: 1, status: 'SHIPPED', total: 129.99, createdAt: '2025-06-05T14:30:00Z' },
        { id: 'ORD-003', userId: user?.id || '1', product: 'Service C', quantity: 1, status: 'PENDING', total: 19.99, createdAt: '2025-06-10T09:15:00Z' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchOrders(); }, []);

  const validate = (): boolean => {
    const errs: FormErrors = {};
    if (!form.product.trim()) errs.product = 'Product name is required';
    const qty = parseInt(form.quantity);
    if (!form.quantity || isNaN(qty) || qty < 1) errs.quantity = 'Quantity must be >= 1';
    const tot = parseFloat(form.total);
    if (!form.total || isNaN(tot) || tot <= 0) errs.total = 'Total must be a positive number';
    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setSaving(true);
    try {
      const order = await createOrder({
        product: form.product.trim(),
        quantity: parseInt(form.quantity),
        total: parseFloat(form.total),
      });
      setOrders((prev) => [...prev, order]);
      setShowCreate(false);
      setForm({ product: '', quantity: '1', total: '' });
    } catch {
      const newOrder: Order = {
        id: `ORD-${String(orders.length + 1).padStart(3, '0')}`,
        userId: user?.id || '1',
        product: form.product.trim(),
        quantity: parseInt(form.quantity),
        status: 'PENDING',
        total: parseFloat(form.total),
        createdAt: new Date().toISOString(),
      };
      setOrders((prev) => [...prev, newOrder]);
      setShowCreate(false);
      setForm({ product: '', quantity: '1', total: '' });
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (id: string, newStatus: Order['status']) => {
    try {
      const updated = await updateOrderStatus(id, newStatus);
      setOrders((prev) => prev.map((o) => (o.id === id ? updated : o)));
    } catch {
      setOrders((prev) => prev.map((o) => (o.id === id ? { ...o, status: newStatus } : o)));
    }
  };

  const nextStatus = (current: Order['status']): Order['status'] | null => {
    const flow: Record<Order['status'], Order['status'] | null> = {
      PENDING: 'CONFIRMED',
      CONFIRMED: 'SHIPPED',
      SHIPPED: 'DELIVERED',
      DELIVERED: null,
      CANCELLED: null,
    };
    return flow[current];
  };

  if (loading) return <div className="page-loading">Loading orders...</div>;

  return (
    <div className="page">
      <div className="page-header">
        <h1>Orders</h1>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>+ New Order</button>
      </div>

      <div className="table-responsive">
        <table className="table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Product</th>
              <th>Qty</th>
              <th>Total</th>
              <th>Status</th>
              <th>Date</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => {
              const next = nextStatus(order.status);
              return (
                <tr key={order.id}>
                  <td><code>{order.id}</code></td>
                  <td>{order.product}</td>
                  <td>{order.quantity}</td>
                  <td>${order.total.toFixed(2)}</td>
                  <td><span className={`badge badge-${statusColors[order.status]}`}>{order.status}</span></td>
                  <td>{new Date(order.createdAt).toLocaleDateString()}</td>
                  <td>
                    {next ? (
                      <button
                        className="btn btn-sm btn-outline"
                        onClick={() => handleStatusChange(order.id, next)}
                      >
                        Move to {next}
                      </button>
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>New Order</h2>
            <form onSubmit={handleCreate} noValidate>
              <div className="form-group">
                <label>Product</label>
                <input
                  value={form.product}
                  onChange={(e) => setForm({ ...form, product: e.target.value })}
                  className={formErrors.product ? 'input-error' : ''}
                  placeholder="Product name"
                />
                {formErrors.product && <span className="field-error">{formErrors.product}</span>}
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Quantity</label>
                  <input
                    type="number"
                    min="1"
                    value={form.quantity}
                    onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                    className={formErrors.quantity ? 'input-error' : ''}
                  />
                  {formErrors.quantity && <span className="field-error">{formErrors.quantity}</span>}
                </div>
                <div className="form-group">
                  <label>Total ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={form.total}
                    onChange={(e) => setForm({ ...form, total: e.target.value })}
                    className={formErrors.total ? 'input-error' : ''}
                    placeholder="0.00"
                  />
                  {formErrors.total && <span className="field-error">{formErrors.total}</span>}
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-outline" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Creating...' : 'Create Order'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
