import {
  adminCsrfHeaders,
  adminJsonHeaders,
  requestAdminJson,
  requestAdminVoid,
} from './adminApi';

const CONTENT_ROOT = '/api/v1/admin/content';
export const ADMIN_CONTENT_PAGE_SIZE = 20;

export type PublishedFilter = '' | 'true' | 'false';

export type AdminNewsListItem = {
  id: number;
  slug: string;
  title: string;
  excerpt: string;
  image_url: string | null;
  is_published: boolean;
  published_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AdminNewsDetail = AdminNewsListItem & { body: string };

export type AdminVideoListItem = {
  id: number;
  title: string;
  description: string;
  source_url: string;
  provider: string;
  is_published: boolean;
  published_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AdminVideoDetail = AdminVideoListItem & { embed_url: string };

export type AdminPageListItem = {
  key: string;
  title: string;
  is_published: boolean;
  updated_at: string;
};

export type AdminPageDetail = AdminPageListItem & {
  content: string;
  created_at: string;
};

type ListResponse<T> = { items: T[]; limit: number; offset: number };
type PageListResponse = { items: AdminPageListItem[] };

export function listAdminNews(params: { published: PublishedFilter; offset: number }, signal?: AbortSignal) {
  return requestAdminJson<ListResponse<AdminNewsListItem>>(`${CONTENT_ROOT}/news?${contentQuery(params)}`, { signal });
}

export function getAdminNews(id: number, signal?: AbortSignal) {
  return requestAdminJson<AdminNewsDetail>(`${CONTENT_ROOT}/news/${id}`, { signal });
}

export function createAdminNews(payload: NewsPayload) {
  return requestAdminJson<AdminNewsDetail>(`${CONTENT_ROOT}/news`, {
    method: 'POST',
    headers: adminJsonHeaders(adminCsrfHeaders()),
    body: JSON.stringify(payload),
  });
}

export function updateAdminNews(id: number, payload: Partial<NewsPayload>) {
  return requestAdminJson<AdminNewsDetail>(`${CONTENT_ROOT}/news/${id}`, {
    method: 'PATCH',
    headers: adminJsonHeaders(adminCsrfHeaders()),
    body: JSON.stringify(payload),
  });
}

export function deleteAdminNews(id: number) {
  return requestAdminVoid(`${CONTENT_ROOT}/news/${id}`, {
    method: 'DELETE',
    headers: adminCsrfHeaders(),
  });
}

export function listAdminVideos(params: { published: PublishedFilter; offset: number }, signal?: AbortSignal) {
  return requestAdminJson<ListResponse<AdminVideoListItem>>(`${CONTENT_ROOT}/videos?${contentQuery(params)}`, { signal });
}

export function getAdminVideo(id: number, signal?: AbortSignal) {
  return requestAdminJson<AdminVideoDetail>(`${CONTENT_ROOT}/videos/${id}`, { signal });
}

export function createAdminVideo(payload: VideoPayload) {
  return requestAdminJson<AdminVideoDetail>(`${CONTENT_ROOT}/videos`, {
    method: 'POST',
    headers: adminJsonHeaders(adminCsrfHeaders()),
    body: JSON.stringify(payload),
  });
}

export function updateAdminVideo(id: number, payload: Partial<VideoPayload>) {
  return requestAdminJson<AdminVideoDetail>(`${CONTENT_ROOT}/videos/${id}`, {
    method: 'PATCH',
    headers: adminJsonHeaders(adminCsrfHeaders()),
    body: JSON.stringify(payload),
  });
}

export function deleteAdminVideo(id: number) {
  return requestAdminVoid(`${CONTENT_ROOT}/videos/${id}`, {
    method: 'DELETE',
    headers: adminCsrfHeaders(),
  });
}

export function listAdminPages(signal?: AbortSignal) {
  return requestAdminJson<PageListResponse>(`${CONTENT_ROOT}/pages`, { signal });
}

export function getAdminPage(key: string, signal?: AbortSignal) {
  return requestAdminJson<AdminPageDetail>(`${CONTENT_ROOT}/pages/${encodeURIComponent(key)}`, { signal });
}

export function updateAdminPage(key: string, payload: Partial<PagePayload>) {
  return requestAdminJson<AdminPageDetail>(`${CONTENT_ROOT}/pages/${encodeURIComponent(key)}`, {
    method: 'PATCH',
    headers: adminJsonHeaders(adminCsrfHeaders()),
    body: JSON.stringify(payload),
  });
}

export type NewsPayload = {
  slug: string;
  title: string;
  excerpt: string;
  body: string;
  image_url: string | null;
  is_published: boolean;
};

export type VideoPayload = {
  title: string;
  description: string;
  source_url: string;
  is_published: boolean;
};

export type PagePayload = {
  title: string;
  content: string;
  is_published: boolean;
};

function contentQuery(params: { published: PublishedFilter; offset: number }) {
  const query = new URLSearchParams({ limit: String(ADMIN_CONTENT_PAGE_SIZE), offset: String(params.offset) });
  if (params.published) {
    query.set('published', params.published);
  }
  return query.toString();
}
