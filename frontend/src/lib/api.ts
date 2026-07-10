// API client for backend communication
// Uses Next.js proxy - all requests go to /api/... and get proxied to backend

import { emitApiError } from './errorEvents';

import type {
  Manuscript,
  Project,
  Idea,
  Paper,
  ResearchRun,
  ResearchReport,
  ResearchQuestion,
  Hypothesis,
  Skill,
  KnowledgeNote,
  ApprovalRequest,
  AuditLog,
  ResearchState,
  ValidationPlan,
  ProjectStats,
  PaperCluster,
  ClusterConflict,
  SemanticSearchResponse,
  AppEvent,
  ToolCall,
  PaperComparison,
  CitationGraph,
  WikiSemanticSearchResponse,
  Comment,
  ProjectMember,
  CollaborationUser,
  ManuscriptTemplate,
  ReviewProposal,
  ActivityItem,
  ArxivSearchResult,
  AuthTokenResponse,
  DomainPack,
  PeerReviewSimulation,
  ReviewNotification,
  WikiGraph,
  PowerAnalysisResult,
  PlotlySandboxResult,
  OAuthProvidersResponse,
  SkillPerformanceStats,
  SkillEvaluateResult,
  PerformanceHistoryEntry,
  SkillEvalHistoryEntry,
  OverallHealth,
} from './types';

type Json = Record<string, unknown>;

interface RequestOptions {
  method?: string;
  body?: Json;
  headers?: Record<string, string>;
}

const AUTH_TOKEN_KEY = 'autoscience_auth_token';
const USER_EMAIL_KEY = 'autoscience_user_email';
const USER_NAME_KEY = 'autoscience_user_name';

export function getAuthHeaders(): Record<string, string> {
  if (typeof window === 'undefined') return {};
  const headers: Record<string, string> = {};
  const token = sessionStorage.getItem(AUTH_TOKEN_KEY);
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  } else {
    const email = localStorage.getItem(USER_EMAIL_KEY) || 'anonymous@local';
    const name = localStorage.getItem(USER_NAME_KEY) || email.split('@')[0];
    headers['X-User-Email'] = email;
    headers['X-User-Name'] = name;
  }
  return headers;
}

export function setAuthSession(token: string, user: CollaborationUser) {
  sessionStorage.setItem(AUTH_TOKEN_KEY, token);
  localStorage.setItem(USER_EMAIL_KEY, user.email);
  localStorage.setItem(USER_NAME_KEY, user.display_name);
}

export function clearAuthSession() {
  sessionStorage.removeItem(AUTH_TOKEN_KEY);
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = 'GET', body, headers = {} } = options;

  // Use relative URL - Next.js proxy will forward to backend
  // Endpoint already includes /api/v1/..., proxy maps /api/* to backend
  const response = await fetch(endpoint, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    const message = error.message || error.detail || `HTTP error ${response.status}`;
    emitApiError(message, response.status);
    throw new Error(message);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// Projects
type JsonRecord = Record<string, unknown>;

export const projectsApi = {
  list: () => request<Project[]>('/api/v1/projects'),
  get: (id: string) => request<Project>(`/api/v1/projects/${id}`),
  create: (data: JsonRecord) => request<Project>('/api/v1/projects', { method: 'POST', body: data }),
  update: (id: string, data: JsonRecord) => request<Project>(`/api/v1/projects/${id}`, { method: 'PUT', body: data }),
  delete: (id: string) => request<void>(`/api/v1/projects/${id}`, { method: 'DELETE' }),
  stats: (id: string) => request<ProjectStats>(`/api/v1/projects/${id}/stats`),
  graph: (id: string) => request<any>(`/api/v1/projects/${id}/graph`),
  idleCycles: (id: string, limit = 20) =>
    request<Json>(`/api/v1/projects/${id}/idle-cycles?limit=${limit}`),
  activity: (id: string, limit = 50) =>
    request<ActivityItem[]>(`/api/v1/projects/${id}/activity?limit=${limit}`),
  auditExportUrl: (id: string, format: 'json' | 'csv' = 'json') =>
    `/api/v1/projects/${id}/audit/export?format=${format}`,
  domainPacks: () => request<DomainPack[]>('/api/v1/projects/domain-packs/list'),
  applyDomainPack: (projectId: string, packId: string) =>
    request<Project>(
      `/api/v1/projects/${projectId}/apply-domain-pack?pack_id=${packId}`,
      { method: 'POST' },
    ),
};

// Ideas
export const ideasApi = {
  list: (projectId: string, params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<Idea[]>(`/api/v1/ideas?project_id=${projectId}${query}`);
  },
  get: (id: string) => request<Idea>(`/api/v1/ideas/${id}`),
  create: (projectId: string, data: JsonRecord) => 
    request<Idea>(`/api/v1/ideas?project_id=${projectId}`, { method: 'POST', body: data }),
  update: (id: string, data: JsonRecord) => 
    request<Idea>(`/api/v1/ideas/${id}`, { method: 'PUT', body: data }),
  delete: (id: string) => request<void>(`/api/v1/ideas/${id}`, { method: 'DELETE' }),
  versions: (id: string) => request<Json[]>(`/api/v1/ideas/${id}/versions`),
  decisions: (id: string) => request<Json[]>(`/api/v1/ideas/${id}/decisions`),
  pause: (id: string) => request<JsonRecord>(`/api/v1/ideas/${id}/pause`, { method: 'POST' }),
  resume: (id: string) => request<JsonRecord>(`/api/v1/ideas/${id}/resume`, { method: 'POST' }),
};

// Research Runs
export const runsApi = {
  list: (projectId: string, params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<ResearchRun[]>(`/api/v1/runs?project_id=${projectId}${query}`);
  },
  get: (id: string) => request<ResearchRun>(`/api/v1/runs/${id}`),
  create: (projectId: string, data: JsonRecord) => 
    request<ResearchRun>(`/api/v1/runs?project_id=${projectId}`, { method: 'POST', body: data }),
  start: (id: string) => request<JsonRecord>(`/api/v1/runs/${id}/start`, { method: 'POST' }),
  pause: (id: string) => request<JsonRecord>(`/api/v1/runs/${id}/pause`, { method: 'POST' }),
  resume: (id: string) => request<JsonRecord>(`/api/v1/runs/${id}/resume`, { method: 'POST' }),
  complete: (id: string) => request<JsonRecord>(`/api/v1/runs/${id}/complete`, { method: 'POST' }),
  cancel: (id: string) => request<JsonRecord>(`/api/v1/runs/${id}/cancel`, { method: 'POST' }),
  events: (id: string) => request<AppEvent[]>(`/api/v1/runs/${id}/events`),
  tools: (id: string) => request<ToolCall[]>(`/api/v1/runs/${id}/tools`),
  status: (id: string) => request<Json>(`/api/v1/runs/${id}/status`),
  byIdea: (ideaId: string) => request<ResearchRun[]>(`/api/v1/runs/by-idea/${ideaId}`),
  snapshot: (id: string) => request<Json>(`/api/v1/runs/${id}/snapshot`),
  delete: (id: string) => request<void>(`/api/v1/runs/${id}`, { method: 'DELETE' }),
  audit: (id: string) => request<Json[]>(`/api/v1/runs/${id}/audit`),
  experiment: (id: string) => request<Json>(`/api/v1/runs/${id}/experiment`),
};

// Papers
export const papersApi = {
  list: (projectId: string, params?: Record<string, string>, clusterId?: string) => {
    const queryParams = { project_id: projectId, ...params };
    if (clusterId) (queryParams as any).cluster_id = clusterId;
    const query = '?' + new URLSearchParams(queryParams as any).toString();
    return request<Paper[]>(`/api/v1/papers${query}`);
  },
  get: (id: string) => request<Paper>(`/api/v1/papers/${id}`),
  create: (projectId: string, data: JsonRecord) => 
    request<Paper>(`/api/v1/papers?project_id=${projectId}`, { method: 'POST', body: data }),
  update: (id: string, data: JsonRecord) => 
    request<Paper>(`/api/v1/papers/${id}`, { method: 'PUT', body: data }),
  delete: (id: string) => request<void>(`/api/v1/papers/${id}`, { method: 'DELETE' }),
  analysis: (id: string) => request<Json>(`/api/v1/papers/${id}/analysis`),
  clusters: (projectId: string, runId?: string) => {
    const query = runId ? `&run_id=${runId}` : '';
    return request<PaperCluster[]>(`/api/v1/papers/clusters?project_id=${projectId}${query}`);
  },
  conflicts: (projectId: string, conflictType?: string, clusterId?: string, runId?: string) => {
    const params: any = { project_id: projectId };
    if (conflictType) params.conflict_type = conflictType;
    if (clusterId) params.cluster_id = clusterId;
    if (runId) params.run_id = runId;
    const query = '?' + new URLSearchParams(params).toString();
    return request<ClusterConflict[]>(`/api/v1/papers/conflicts${query}`);
  },
  semanticSearch: (projectId: string, q: string, limit = 10) =>
    request<SemanticSearchResponse>(
      `/api/v1/papers/search/semantic?project_id=${projectId}&q=${encodeURIComponent(q)}&limit=${limit}`
    ),
  compare: (ids: string[]) =>
    request<PaperComparison>(`/api/v1/papers/compare?ids=${ids.join(',')}`),
  citationGraph: (projectId: string) =>
    request<CitationGraph>(`/api/v1/papers/citation-graph?project_id=${projectId}`),
  arxivSearch: (q: string, limit = 20) =>
    request<{ query: string; papers: ArxivSearchResult[] }>(
      `/api/v1/papers/arxiv/search?q=${encodeURIComponent(q)}&limit=${limit}`,
    ),
  resolveDoi: (projectId: string, doi: string) =>
    request<Paper>(
      `/api/v1/papers/resolve-doi?project_id=${projectId}&doi=${encodeURIComponent(doi)}`,
      { method: 'POST' },
    ),
  importArxiv: (projectId: string, sourceId: string) =>
    request<Paper>(
      `/api/v1/papers/import-arxiv?project_id=${projectId}&source_id=${encodeURIComponent(sourceId)}`,
      { method: 'POST' },
    ),
};

// Skills
export const skillsApi = {
  list: (params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<Skill[]>(`/api/v1/skills${query}`);
  },
  get: (id: string) => request<Skill>(`/api/v1/skills/${id}`),
  create: (data: JsonRecord) => request<Skill>('/api/v1/skills', { method: 'POST', body: data }),
  update: (id: string, data: JsonRecord) => 
    request<Skill>(`/api/v1/skills/${id}`, { method: 'PUT', body: data }),
  delete: (id: string) => request<void>(`/api/v1/skills/${id}`, { method: 'DELETE' }),
  retire: (id: string) => request<JsonRecord>(`/api/v1/skills/${id}/retire`, { method: 'POST' }),
  versions: (id: string) => request<Json[]>(`/api/v1/skills/${id}/versions`),
  usage: (id: string) => request<Json[]>(`/api/v1/skills/${id}/usage`),
  evaluate: (data: { dry_run?: boolean; project_id?: string }) =>
    request<SkillEvaluateResult>('/api/v1/skills/evaluate', { method: 'POST', body: data as JsonRecord }),
  performanceStats: (projectId?: string) => {
    const query = projectId ? `?project_id=${projectId}` : '';
    return request<SkillPerformanceStats>(`/api/v1/skills/performance/stats${query}`);
  },
  performanceHistory: (params?: { project_id?: string; skill_id?: string; limit?: number }) => {
    const query = params ? '?' + new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([_, v]) => v !== undefined).map(([k, v]) => [k, String(v)]))
    ).toString() : '';
    return request<PerformanceHistoryEntry[]>(`/api/v1/skills/performance/history${query}`);
  },
  schedulerConfig: () => request<JsonRecord>('/api/v1/skills/performance/scheduler-config'),
  schedulerStatus: () => request<JsonRecord>('/api/v1/skills/performance/scheduler-status'),
  updateSchedulerConfig: (data: { enabled?: boolean; interval_hours?: number; dry_run?: boolean }) =>
    request<JsonRecord>('/api/v1/skills/performance/scheduler-config', { method: 'PATCH', body: data }),
  evalHistory: (params?: { limit?: number }) => {
    const query = params?.limit ? `?limit=${params.limit}` : '';
    return request<SkillEvalHistoryEntry[]>(`/api/v1/skills/performance/eval-history${query}`);
  },
};

// Research Questions
export const questionsApi = {
  list: (projectId: string, params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<ResearchQuestion[]>(`/api/v1/questions?project_id=${projectId}${query}`);
  },
  get: (id: string) => request<ResearchQuestion>(`/api/v1/questions/${id}`),
  create: (projectId: string, data: JsonRecord) => 
    request<ResearchQuestion>(`/api/v1/questions?project_id=${projectId}`, { method: 'POST', body: data }),
  reject: (id: string, reason: string) => 
    request<JsonRecord>(`/api/v1/questions/${id}/reject?reason=${encodeURIComponent(reason)}`, { method: 'POST' }),
};

// Hypotheses
export const hypothesesApi = {
  list: (projectId: string, params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<Hypothesis[]>(`/api/v1/hypotheses?project_id=${projectId}${query}`);
  },
  get: (id: string) => request<Hypothesis>(`/api/v1/hypotheses/${id}`),
  create: (projectId: string, data: JsonRecord) => 
    request<Hypothesis>(`/api/v1/hypotheses?project_id=${projectId}`, { method: 'POST', body: data }),
  update: (id: string, data: JsonRecord) => 
    request<Hypothesis>(`/api/v1/hypotheses/${id}`, { method: 'PUT', body: data }),
  validation: (id: string) => request<ValidationPlan>(`/api/v1/hypotheses/${id}/validation`),
};

// Reports
export const reportsApi = {
  list: (projectId: string) => request<ResearchReport[]>(`/api/v1/reports?project_id=${projectId}`),
  get: (id: string) => request<ResearchReport>(`/api/v1/reports/${id}`),
  delete: (id: string) => request<void>(`/api/v1/reports/${id}`, { method: 'DELETE' }),
};

// Wiki
export const wikiApi = {
  list: (projectId: string, params?: { note_type?: string; run_id?: string }) => {
    const query = new URLSearchParams({ project_id: projectId });
    if (params?.note_type) query.set('note_type', params.note_type);
    if (params?.run_id) query.set('run_id', params.run_id);
    return request<KnowledgeNote[]>(`/api/v1/wiki?${query.toString()}`);
  },
  search: (projectId: string, q: string, runId?: string) => {
    const query = new URLSearchParams({ project_id: projectId, q });
    if (runId) query.set('run_id', runId);
    return request<KnowledgeNote[]>(`/api/v1/wiki/search?${query.toString()}`);
  },
  get: (id: string) => request<KnowledgeNote>(`/api/v1/wiki/${id}`),
  create: (projectId: string, data: JsonRecord) => 
    request<KnowledgeNote>(`/api/v1/wiki?project_id=${projectId}`, { method: 'POST', body: data }),
  update: (id: string, data: JsonRecord) => 
    request<KnowledgeNote>(`/api/v1/wiki/${id}`, { method: 'PUT', body: data }),
  delete: (id: string) => request<void>(`/api/v1/wiki/${id}`, { method: 'DELETE' }),
  semanticSearch: (projectId: string, q: string, runId?: string, limit = 20) => {
    const query = new URLSearchParams({ project_id: projectId, q, limit: String(limit) });
    if (runId) query.set('run_id', runId);
    return request<WikiSemanticSearchResponse>(`/api/v1/wiki/search/semantic?${query.toString()}`);
  },
  graph: (projectId: string) =>
    request<WikiGraph>(`/api/v1/wiki/graph?project_id=${projectId}`),
};

// Approvals
export const approvalsApi = {
  list: (projectId: string) => request<ApprovalRequest[]>(`/api/v1/approvals?project_id=${projectId}`),
  approve: (id: string, notes?: string) => 
    request<JsonRecord>(`/api/v1/approvals/${id}/approve`, { method: 'POST', body: { approved: true, reviewer_notes: notes } }),
  deny: (id: string, reason: string) => 
    request<JsonRecord>(`/api/v1/approvals/${id}/deny`, { method: 'POST', body: { approved: false, reviewer_notes: reason } }),
};

export const datasetsApi = {
  list: (projectId: string) => request<Json[]>(`/api/v1/datasets?project_id=${projectId}`),
  search: (query: string, limit = 20) =>
    request<Json[]>(
      `/api/v1/datasets/search?query=${encodeURIComponent(query)}&limit=${limit}`,
    ),
  previewExternal: (source: string, identifier: string) =>
    request<JsonRecord>(
      `/api/v1/datasets/external?source=${encodeURIComponent(source)}&identifier=${encodeURIComponent(identifier)}`,
    ),
  create: (data: JsonRecord) =>
    request<JsonRecord>(`/api/v1/datasets`, { method: 'POST', body: data }),
  get: (id: string) => request<JsonRecord>(`/api/v1/datasets/${id}`),
  update: (id: string, data: JsonRecord) =>
    request<JsonRecord>(`/api/v1/datasets/${id}`, { method: 'PUT', body: data }),
  delete: (id: string) =>
    request<JsonRecord>(`/api/v1/datasets/${id}`, { method: 'DELETE' }),
  upload: async (formData: FormData) => {
    const headers = getAuthHeaders();
    delete headers['Content-Type'];  // Let browser set multipart boundary
    const response = await fetch('/api/v1/datasets/upload', {
      method: 'POST',
      body: formData,
      headers,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }
    return response.json();
  },
  exportUrl: (projectId: string, format: 'json' | 'csv') =>
    `/api/v1/datasets/export?project_id=${projectId}&format=${format}`,
};

export const authApi = {
  token: (email: string, displayName?: string) =>
    request<AuthTokenResponse>('/api/v1/auth/token', {
      method: 'POST',
      body: { email, display_name: displayName },
    }),
  me: () => request<CollaborationUser>('/api/v1/auth/me'),
  oauthProviders: () => request<OAuthProvidersResponse>('/api/v1/auth/oauth/providers'),
  oauthAuthorize: (provider: string) =>
    request<{ provider: string; url: string; state: string }>(
      `/api/v1/auth/oauth/${provider}/authorize`,
    ),
  oauthCallback: (provider: string, code: string, state?: string) =>
    request<AuthTokenResponse>(`/api/v1/auth/oauth/${provider}/callback`, {
      method: 'POST',
      body: { code, state },
    }),
};

export const collaborationApi = {
  me: () => request<CollaborationUser>('/api/v1/collaboration/users/me'),
  listMembers: (projectId: string) =>
    request<ProjectMember[]>(`/api/v1/collaboration/members?project_id=${projectId}`),
  addMember: (data: {
    project_id: string;
    email: string;
    display_name?: string;
    role?: string;
  }) =>
    request<ProjectMember>('/api/v1/collaboration/members', {
      method: 'POST',
      body: data,
    }),
  listComments: (projectId: string, entityType?: string, entityId?: string) => {
    const query = new URLSearchParams({ project_id: projectId });
    if (entityType) query.set('entity_type', entityType);
    if (entityId) query.set('entity_id', entityId);
    return request<Comment[]>(`/api/v1/collaboration/comments?${query.toString()}`);
  },
  createComment: (data: {
    project_id: string;
    entity_type: string;
    entity_id: string;
    body: string;
  }) =>
    request<Comment>('/api/v1/collaboration/comments', {
      method: 'POST',
      body: data,
    }),
  listReviews: (projectId: string, status?: string) => {
    const query = new URLSearchParams({ project_id: projectId });
    if (status) query.set('status', status);
    return request<ReviewProposal[]>(`/api/v1/collaboration/reviews?${query.toString()}`);
  },
  createReview: (data: {
    project_id: string;
    title: string;
    description?: string;
    entity_type: string;
    entity_id?: string;
    assignee_id?: string;
  }) =>
    request<ReviewProposal>('/api/v1/collaboration/reviews', {
      method: 'POST',
      body: data,
    }),
  updateReview: (
    proposalId: string,
    data: { status?: string; assignee_id?: string },
  ) =>
    request<ReviewProposal>(`/api/v1/collaboration/reviews/${proposalId}`, {
      method: 'PATCH',
      body: data,
    }),
  activity: (projectId: string, limit = 50) =>
    request<ActivityItem[]>(
      `/api/v1/collaboration/activity?project_id=${projectId}&limit=${limit}`,
    ),
  simulateReview: (proposalId: string) =>
    request<PeerReviewSimulation>(
      `/api/v1/collaboration/reviews/${proposalId}/simulate`,
      { method: 'POST' },
    ),
  notifications: (projectId: string) =>
    request<ReviewNotification[]>(
      `/api/v1/collaboration/notifications?project_id=${projectId}`,
    ),
};

export function exportReportUrl(reportId: string, format: 'markdown' | 'html' | 'json' = 'markdown'): string {
  return `/api/v1/reports/${reportId}/export?format=${format}`;
}

export const idleApi = {
  trigger: (projectId: string) =>
    request<Json>(`/api/v1/research/idle?project_id=${projectId}`, { method: 'POST' }),
};

export const schedulerApi = {
  status: () => request<Json>('/api/v1/scheduler/status'),
};

export const connectorsApi = {
  health: () => request<Json>('/api/v1/connectors/health'),
  resetCircuit: (name: string) =>
    request<{ success: boolean; source: string; previous_state: string }>(
      `/api/v1/connectors/${encodeURIComponent(name)}/reset`,
      { method: 'POST' },
    ),
};

export const healthApi = {
  check: () => request<OverallHealth>('/api/v1/health'),
};

export const activityApi = {
  track: (projectId: string) =>
    request<Json>(`/api/v1/activity?project_id=${projectId}`, { method: 'POST' }),
};

// Research Control
export const researchApi = {
  start: (data: { project_id: string; idea: string; run_type: string; flexibility: number }) => 
    request<any>('/api/v1/research/run', { method: 'POST', body: data as any }),
};

// Manuscripts
export const manuscriptsApi = {
  list: (projectId: string, runId?: string) => {
    const query = new URLSearchParams({ project_id: projectId });
    if (runId) query.set('run_id', runId);
    return request<Manuscript[]>(`/api/v1/manuscripts?${query.toString()}`);
  },
  get: (id: string) => request<Manuscript>(`/api/v1/manuscripts/${id}`),
  create: (data: { project_id: string; run_id?: string; title: string }) =>
    request<Manuscript>('/api/v1/manuscripts', { method: 'POST', body: data }),
  generate: (runId: string) => request<Manuscript>(`/api/v1/manuscripts/generate?run_id=${runId}`, { method: 'POST' }),
  update: (id: string, data: any) => request<Manuscript>(`/api/v1/manuscripts/${id}`, { method: 'PATCH', body: data }),
  finalize: (id: string) => request<Manuscript>(`/api/v1/manuscripts/${id}/finalize`, { method: 'POST' }),
  compile: (id: string) => request<Manuscript>(`/api/v1/manuscripts/${id}/compile`, { method: 'POST' }),
  download: (id: string, format: 'tex' | 'bib' | 'zip' | 'pdf' = 'tex') =>
    `/api/v1/manuscripts/${id}/download?format=${format}`,
  templates: () => request<ManuscriptTemplate[]>('/api/v1/manuscripts/templates/list'),
  applyTemplate: (manuscriptId: string, templateId: string) =>
    request<Manuscript>(
      `/api/v1/manuscripts/${manuscriptId}/apply-template?template_id=${templateId}`,
      { method: 'POST' },
    ),
};

// Sandbox scripts
export const sandboxApi = {
  generateScript: (hypothesisId: string) => request<any>(`/api/v1/hypotheses/${hypothesisId}/generate-script`, { method: 'POST' }),
  powerAnalysis: (data: {
    project_id: string;
    test_type: 'two_sample_ttest' | 'two_proportion';
    effect_size?: number;
    p1?: number;
    p2?: number;
    alpha?: number;
    power?: number;
  }) =>
    request<PowerAnalysisResult>('/api/v1/sandbox/power-analysis', {
      method: 'POST',
      body: data,
    }),
  plotly: (data: { project_id: string; code: string; title?: string }) =>
    request<PlotlySandboxResult>('/api/v1/sandbox/plotly', {
      method: 'POST',
      body: data,
    }),
  notebookUrl: (runId: string) => `/api/v1/runs/${runId}/notebook`,
};
