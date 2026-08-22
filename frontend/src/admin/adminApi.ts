const API_ROOT = '/api/v1';
const ADMIN_AUTH_ROOT = `${API_ROOT}/admin/auth`;
const ADMIN_CANDIDATES_ROOT = `${API_ROOT}/admin/candidates`;
const CSRF_COOKIE_NAME = 'astrea_admin_csrf';
const CSRF_HEADER_NAME = 'X-CSRF-Token';

export const ADMIN_CANDIDATE_STATUSES = ['new', 'in_review', 'contacted', 'closed', 'archived'] as const;

export type AdminCandidateStatus = (typeof ADMIN_CANDIDATE_STATUSES)[number];

export type AdminAuthResponse = {
  authenticated: boolean;
  username: string;
};

export type AdminCandidateListItem = {
  id: number;
  full_name: string | null;
  city: string | null;
  email: string | null;
  phone: string | null;
  status: AdminCandidateStatus;
  has_photo: boolean;
  created_at: string;
  updated_at: string;
};

export type AdminCandidateListResponse = {
  items: AdminCandidateListItem[];
  limit: number;
  offset: number;
};

export type AdminCandidateConsent = {
  consent_type: string;
  accepted_at: string;
  document_version: string;
};

export type AdminCandidateDetail = {
  id: number;
  full_name: string | null;
  date_of_birth: string | null;
  city: string | null;
  phone: string | null;
  email: string | null;
  education: string | null;
  occupation: string | null;
  marital_status: string | null;
  other_organizations: string | null;
  social_links: string | null;
  motivation: string | null;
  status: AdminCandidateStatus;
  has_photo: boolean;
  created_at: string;
  updated_at: string;
  consents: AdminCandidateConsent[];
};

export type AdminCandidateStatusResponse = {
  id: number;
  status: AdminCandidateStatus;
};

export class AdminApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'AdminApiError';
    this.status = status;
    this.detail = detail;
  }
}

export async function getCurrentAdmin(signal?: AbortSignal): Promise<AdminAuthResponse> {
  return requestJson<AdminAuthResponse>(`${ADMIN_AUTH_ROOT}/me`, { signal });
}

export async function loginAdmin(username: string, password: string): Promise<AdminAuthResponse> {
  return requestJson<AdminAuthResponse>(`${ADMIN_AUTH_ROOT}/login`, {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify({ username, password }),
  });
}

export async function logoutAdmin(signal?: AbortSignal): Promise<void> {
  await requestVoid(`${ADMIN_AUTH_ROOT}/logout`, {
    method: 'POST',
    headers: csrfHeaders(),
    signal,
  });
}

export async function listAdminCandidates(
  params: { limit?: number; offset?: number; status?: AdminCandidateStatus | '' },
  signal?: AbortSignal,
): Promise<AdminCandidateListResponse> {
  const query = new URLSearchParams();
  query.set('limit', String(params.limit ?? 20));
  query.set('offset', String(params.offset ?? 0));
  if (params.status) {
    query.set('status', params.status);
  }
  return requestJson<AdminCandidateListResponse>(`${ADMIN_CANDIDATES_ROOT}?${query.toString()}`, { signal });
}

export async function getAdminCandidate(id: number, signal?: AbortSignal): Promise<AdminCandidateDetail> {
  return requestJson<AdminCandidateDetail>(`${ADMIN_CANDIDATES_ROOT}/${id}`, { signal });
}

export async function getAdminCandidatePhoto(id: number, signal?: AbortSignal): Promise<Blob> {
  return requestBlob(`${ADMIN_CANDIDATES_ROOT}/${id}/photo`, { signal });
}

export async function updateAdminCandidateStatus(
  id: number,
  status: AdminCandidateStatus,
): Promise<AdminCandidateStatusResponse> {
  return requestJson<AdminCandidateStatusResponse>(`${ADMIN_CANDIDATES_ROOT}/${id}/status`, {
    method: 'PATCH',
    headers: jsonHeaders({ ...csrfHeaders() }),
    body: JSON.stringify({ status }),
  });
}

function jsonHeaders(headers: HeadersInit = {}): HeadersInit {
  return {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    ...headers,
  };
}

function csrfHeaders(): HeadersInit {
  const token = getCookieValue(CSRF_COOKIE_NAME);
  return token ? { [CSRF_HEADER_NAME]: token } : {};
}

async function requestJson<T>(url: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(url, {
    credentials: 'same-origin',
    ...init,
    headers: mergeHeaders({ Accept: 'application/json' }, init.headers),
  });
  if (!response.ok) {
    throw await createApiError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function requestVoid(url: string, init: RequestInit = {}): Promise<void> {
  const response = await fetch(url, {
    credentials: 'same-origin',
    ...init,
    headers: mergeHeaders({ Accept: 'application/json' }, init.headers),
  });
  if (!response.ok) {
    throw await createApiError(response);
  }
}

async function requestBlob(url: string, init: RequestInit = {}): Promise<Blob> {
  const response = await fetch(url, {
    credentials: 'same-origin',
    ...init,
  });
  if (!response.ok) {
    throw await createApiError(response);
  }
  return await response.blob();
}

async function createApiError(response: Response): Promise<AdminApiError> {
  let detail = response.statusText || 'Request failed';
  const text = await response.text();
  if (text) {
    try {
      const parsed = JSON.parse(text) as unknown;
      if (isDetailResponse(parsed)) {
        detail = parsed.detail;
      } else if (typeof parsed === 'string') {
        detail = parsed;
      }
    } catch {
      detail = text;
    }
  }
  return new AdminApiError(response.status, detail);
}

function isDetailResponse(value: unknown): value is { detail: string } {
  return typeof value === 'object' && value !== null && 'detail' in value && typeof (value as { detail?: unknown }).detail === 'string';
}

function mergeHeaders(base: HeadersInit, override?: HeadersInit): HeadersInit {
  return {
    ...base,
    ...(override ?? {}),
  };
}

function getCookieValue(name: string): string | null {
  const cookies = document.cookie ? document.cookie.split('; ') : [];
  for (const cookie of cookies) {
    const separator = cookie.indexOf('=');
    const key = separator >= 0 ? cookie.slice(0, separator) : cookie;
    if (key === name) {
      return decodeURIComponent(separator >= 0 ? cookie.slice(separator + 1) : '');
    }
  }
  return null;
}
