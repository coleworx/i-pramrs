import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// Use relative path — Vite proxies /api → Flask on port 5000 during dev
export const API_BASE = '/api';


export async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

export const SEV_CLASSES = {
  Low: 'severity-low',
  Medium: 'severity-medium',
  High: 'severity-high',
  Critical: 'severity-critical',
};

export const SEV_DOT = {
  Low: 'bg-emerald-500',
  Medium: 'bg-amber-500',
  High: 'bg-orange-500',
  Critical: 'bg-red-500',
};
