const API_URL = import.meta.env.VITE_API_URL || '';

export async function checkHealth() {
  const res = await fetch(`${API_URL}/api/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function createTask(goal, simulateFailure = false) {
  const res = await fetch(`${API_URL}/api/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goal, simulate_failure: simulateFailure })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to create task');
  }
  return res.json();
}

export async function getTaskStatus(taskId) {
  const res = await fetch(`${API_URL}/api/tasks/${taskId}`);
  if (!res.ok) throw new Error(`Failed to fetch task ${taskId}`);
  return res.json();
}

export async function getTaskEvents(taskId) {
  const res = await fetch(`${API_URL}/api/tasks/${taskId}/events`);
  if (!res.ok) throw new Error(`Failed to fetch events for task ${taskId}`);
  return res.json();
}

export async function approveTask(taskId, feedback = '') {
  const res = await fetch(`${API_URL}/api/tasks/${taskId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ feedback })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Approval request failed');
  }
  return res.json();
}

export async function rejectTask(taskId, reason = '') {
  const res = await fetch(`${API_URL}/api/tasks/${taskId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Rejection request failed');
  }
  return res.json();
}

export async function getTaskResult(taskId) {
  const res = await fetch(`${API_URL}/api/tasks/${taskId}/result`);
  if (!res.ok) throw new Error(`Failed to fetch result for task ${taskId}`);
  return res.json();
}

export async function getFinanceInvoices() {
  const res = await fetch(`${API_URL}/api/finance/api/invoices`);
  if (!res.ok) throw new Error('Failed to fetch finance records');
  return res.json();
}
