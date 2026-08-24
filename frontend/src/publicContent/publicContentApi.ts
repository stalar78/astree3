const PUBLIC_CONTENT_ROOT = '/api/v1';

export type PublicNewsListItem = {
  slug: string;
  title: string;
  excerpt: string;
  image_url: string | null;
  published_at: string | null;
};

export type PublicNewsArticle = PublicNewsListItem & {
  body: string;
};

export type PublicPage = {
  key: string;
  title: string;
  content: string;
};

export type PublicVideo = {
  id: number;
  title: string;
  description: string;
  source_url: string;
  provider: string;
  embed_url: string;
  published_at: string | null;
};

export class PublicContentApiError extends Error {
  readonly status: number;

  constructor(status: number) {
    super('Public content request failed');
    this.name = 'PublicContentApiError';
    this.status = status;
  }
}

export async function listPublicNews(signal?: AbortSignal): Promise<PublicNewsListItem[]> {
  return requestPublicJson<PublicNewsListItem[]>(`${PUBLIC_CONTENT_ROOT}/news`, signal);
}

export async function getPublicNews(slug: string, signal?: AbortSignal): Promise<PublicNewsArticle> {
  return requestPublicJson<PublicNewsArticle>(`${PUBLIC_CONTENT_ROOT}/news/${encodeURIComponent(slug)}`, signal);
}

export async function getPublicPage(key: string, signal?: AbortSignal): Promise<PublicPage> {
  return requestPublicJson<PublicPage>(`${PUBLIC_CONTENT_ROOT}/pages/${encodeURIComponent(key)}`, signal);
}

export async function listPublicVideos(signal?: AbortSignal): Promise<PublicVideo[]> {
  return requestPublicJson<PublicVideo[]>(`${PUBLIC_CONTENT_ROOT}/videos`, signal);
}

async function requestPublicJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, {
    credentials: 'same-origin',
    signal,
  });

  if (!response.ok) {
    throw new PublicContentApiError(response.status);
  }

  return (await response.json()) as T;
}
