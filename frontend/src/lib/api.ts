// API client for backend communication
// Uses Next.js proxy - all requests go to /api/... and get proxied to backend

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
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
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || `HTTP error ${response.status}`);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// Projects
export const projectsApi = {
  list: () => request<any[]>('/api/v1/projects'),
  get: (id: string) => request<any>(`/api/v1/projects/${id}`),
  create: (data: any) => request<any>('/api/v1/projects', { method: 'POST', body: data }),
  update: (id: string, data: any) => request<any>(`/api/v1/projects/${id}`, { method: 'PUT', body: data }),
  delete: (id: string) => request<void>(`/api/v1/projects/${id}`, { method: 'DELETE' }),
  stats: (id: string) => request<any>(`/api/v1/projects/${id}/stats`),
};

// Ideas
export const ideasApi = {
  list: (projectId: string, params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<any[]>(`/api/v1/ideas?project_id=${projectId}${query}`);
  },
  get: (id: string) => request<any>(`/api/v1/ideas/${id}`),
  create: (projectId: string, data: any) => 
    request<any>(`/api/v1/ideas?project_id=${projectId}`, { method: 'POST', body: data }),
  update: (id: string, data: any) => 
    request<any>(`/api/v1/ideas/${id}`, { method: 'PUT', body: data }),
  delete: (id: string) => request<void>(`/api/v1/ideas/${id}`, { method: 'DELETE' }),
  versions: (id: string) => request<any[]>(`/api/v1/ideas/${id}/versions`),
  decisions: (id: string) => request<any[]>(`/api/v1/ideas/${id}/decisions`),
  pause: (id: string) => request<any>(`/api/v1/ideas/${id}/pause`, { method: 'POST' }),
  resume: (id: string) => request<any>(`/api/v1/ideas/${id}/resume`, { method: 'POST' }),
};

// Research Runs
export const runsApi = {
  list: (projectId: string, params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<any[]>(`/api/v1/runs?project_id=${projectId}${query}`);
  },
  get: (id: string) => request<any>(`/api/v1/runs/${id}`),
  create: (projectId: string, data: any) => 
    request<any>(`/api/v1/runs?project_id=${projectId}`, { method: 'POST', body: data }),
  start: (id: string) => request<any>(`/api/v1/runs/${id}/start`, { method: 'POST' }),
  pause: (id: string) => request<any>(`/api/v1/runs/${id}/pause`, { method: 'POST' }),
  resume: (id: string) => request<any>(`/api/v1/runs/${id}/resume`, { method: 'POST' }),
  complete: (id: string) => request<any>(`/api/v1/runs/${id}/complete`, { method: 'POST' }),
  cancel: (id: string) => request<any>(`/api/v1/runs/${id}/cancel`, { method: 'POST' }),
  events: (id: string) => request<any[]>(`/api/v1/runs/${id}/events`),
  tools: (id: string) => request<any[]>(`/api/v1/runs/${id}/tools`),
  status: (id: string) => request<any>(`/api/v1/runs/${id}/status`),
  byIdea: (ideaId: string) => request<any[]>(`/api/v1/runs/by-idea/${ideaId}`),
  snapshot: (id: string) => request<any>(`/api/v1/runs/${id}/snapshot`),
  delete: (id: string) => request<void>(`/api/v1/runs/${id}`, { method: 'DELETE' }),
};

// Papers
export const papersApi = {
  list: (projectId: string, params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<any[]>(`/api/v1/papers?project_id=${projectId}${query}`);
  },
  get: (id: string) => request<any>(`/api/v1/papers/${id}`),
  create: (projectId: string, data: any) => 
    request<any>(`/api/v1/papers?project_id=${projectId}`, { method: 'POST', body: data }),
  update: (id: string, data: any) => 
    request<any>(`/api/v1/papers/${id}`, { method: 'PUT', body: data }),
  delete: (id: string) => request<void>(`/api/v1/papers/${id}`, { method: 'DELETE' }),
  analysis: (id: string) => request<any>(`/api/v1/papers/${id}/analysis`),
  clusters: (projectId: string) => request<any[]>(`/api/v1/papers/clusters?project_id=${projectId}`),
  conflicts: (projectId: string) => request<any[]>(`/api/v1/papers/conflicts?project_id=${projectId}`),
};

// Skills
export const skillsApi = {
  list: (params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<any[]>(`/api/v1/skills${query}`);
  },
  get: (id: string) => request<any>(`/api/v1/skills/${id}`),
  create: (data: any) => request<any>('/api/v1/skills', { method: 'POST', body: data }),
  update: (id: string, data: any) => 
    request<any>(`/api/v1/skills/${id}`, { method: 'PUT', body: data }),
  delete: (id: string) => request<void>(`/api/v1/skills/${id}`, { method: 'DELETE' }),
  retire: (id: string) => request<any>(`/api/v1/skills/${id}/retire`, { method: 'POST' }),
  versions: (id: string) => request<any[]>(`/api/v1/skills/${id}/versions`),
  usage: (id: string) => request<any[]>(`/api/v1/skills/${id}/usage`),
};

// Research Questions
export const questionsApi = {
  list: (projectId: string, params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<any[]>(`/api/v1/questions?project_id=${projectId}${query}`);
  },
  get: (id: string) => request<any>(`/api/v1/questions/${id}`),
  create: (projectId: string, data: any) => 
    request<any>(`/api/v1/questions?project_id=${projectId}`, { method: 'POST', body: data }),
  reject: (id: string, reason: string) => 
    request<any>(`/api/v1/questions/${id}/reject?reason=${encodeURIComponent(reason)}`, { method: 'POST' }),
};

// Hypotheses
export const hypothesesApi = {
  list: (projectId: string, params?: Record<string, string>) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<any[]>(`/api/v1/hypotheses?project_id=${projectId}${query}`);
  },
  get: (id: string) => request<any>(`/api/v1/hypotheses/${id}`),
  create: (projectId: string, data: any) => 
    request<any>(`/api/v1/hypotheses?project_id=${projectId}`, { method: 'POST', body: data }),
  update: (id: string, data: any) => 
    request<any>(`/api/v1/hypotheses/${id}`, { method: 'PUT', body: data }),
  validation: (id: string) => request<any>(`/api/v1/hypotheses/${id}/validation`),
};

// Reports
export const reportsApi = {
  list: (projectId: string) => request<any[]>(`/api/v1/reports?project_id=${projectId}`),
  get: (id: string) => request<any>(`/api/v1/reports/${id}`),
  delete: (id: string) => request<void>(`/api/v1/reports/${id}`, { method: 'DELETE' }),
};

// Wiki
export const wikiApi = {
  list: (projectId: string) => request<any[]>(`/api/v1/wiki?project_id=${projectId}`),
  get: (id: string) => request<any>(`/api/v1/wiki/${id}`),
  create: (projectId: string, data: any) => 
    request<any>(`/api/v1/wiki?project_id=${projectId}`, { method: 'POST', body: data }),
  update: (id: string, data: any) => 
    request<any>(`/api/v1/wiki/${id}`, { method: 'PUT', body: data }),
  delete: (id: string) => request<void>(`/api/v1/wiki/${id}`, { method: 'DELETE' }),
};

// Approvals
export const approvalsApi = {
  list: (projectId: string) => request<any[]>(`/api/v1/approvals?project_id=${projectId}`),
  approve: (id: string, notes?: string) => 
    request<any>(`/api/v1/approvals/${id}/approve`, { method: 'POST', body: { approved: true, reviewer_notes: notes } }),
  deny: (id: string, reason: string) => 
    request<any>(`/api/v1/approvals/${id}/deny`, { method: 'POST', body: { approved: false, reviewer_notes: reason } }),
};
