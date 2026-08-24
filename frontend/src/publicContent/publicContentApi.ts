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
