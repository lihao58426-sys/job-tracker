import axios from 'axios';
import type { Application, ApplicationListItem, DashboardStats, FunnelItem } from './types';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

// ============================================================
// 岗位 CRUD
// ============================================================

export async function fetchJobs(params?: Record<string, string>) {
  const { data } = await api.get<ApplicationListItem[]>('/jobs', { params });
  return data;
}

export async function fetchJob(id: string) {
  const { data } = await api.get<Application>(`/jobs/${id}`);
  return data;
}

export async function createJob(job: Record<string, unknown>) {
  const { data } = await api.post<Application>('/jobs', job);
  return data;
}

export async function updateJob(id: string, updates: Record<string, unknown>) {
  const { data } = await api.put<Application>(`/jobs/${id}`, updates);
  return data;
}

export async function updateJobStatus(id: string, status: string, note = '') {
  const { data } = await api.put<Application>(`/jobs/${id}/status`, { status, note });
  return data;
}

export async function deleteJob(id: string) {
  await api.delete(`/jobs/${id}`);
}

export async function batchDeleteJobs(ids: string[]) {
  const { data } = await api.post('/jobs/batch-delete', { ids });
  return data;
}

// ============================================================
// 统计
// ============================================================

export async function fetchDashboard() {
  const { data } = await api.get<DashboardStats>('/stats/dashboard');
  return data;
}

export async function fetchFunnel() {
  const { data } = await api.get<FunnelItem[]>('/stats/funnel');
  return data;
}

// ============================================================
// 导入
// ============================================================

export async function importBatch(jobs: Record<string, unknown>[]) {
  const { data } = await api.post('/import/batch', jobs);
  return data;
}
