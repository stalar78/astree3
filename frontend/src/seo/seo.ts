const INDEX_ROBOTS = 'index, follow';
const NOINDEX_ROBOTS = 'noindex, nofollow, noarchive';
const META_DESCRIPTION_LIMIT = 160;

export type DocumentSeo = {
  title: string;
  description: string;
  pathname: string;
  indexable?: boolean;
};

export function applyDocumentSeo({
  title,
  description,
  pathname,
  indexable = true,
}: DocumentSeo) {
  document.title = title;
  setNamedMeta('description', description);
  setDocumentIndexability(pathname, indexable);
}

export function setDocumentIndexability(pathname: string, indexable: boolean) {
  setNamedMeta('robots', indexable ? INDEX_ROBOTS : NOINDEX_ROBOTS);

  const canonicalHref = indexable ? buildCanonicalHref(pathname) : null;
  let canonical = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');

  if (!canonicalHref) {
    canonical?.remove();
    return;
  }

  if (!canonical) {
    canonical = document.createElement('link');
    canonical.rel = 'canonical';
    document.head.appendChild(canonical);
  }
  canonical.href = canonicalHref;
}

export function siteTitle(title: string) {
  return title === 'Astrea' ? title : `${title} | Astrea`;
}

export function seoDescriptionFromText(value: string, fallback: string) {
  const normalized = value.replace(/\s+/g, ' ').trim();
  if (!normalized) return fallback;
  if (normalized.length <= META_DESCRIPTION_LIMIT) return normalized;
  return `${normalized.slice(0, META_DESCRIPTION_LIMIT - 1).trimEnd()}…`;
}

function setNamedMeta(name: string, content: string) {
  let element = document.querySelector<HTMLMetaElement>(`meta[name="${name}"]`);
  if (!element) {
    element = document.createElement('meta');
    element.name = name;
    document.head.appendChild(element);
  }
  element.content = content;
}

function buildCanonicalHref(pathname: string): string | null {
  const origin = configuredPublicOrigin();
  if (!origin) return null;

  const leadingSlashPath = pathname.startsWith('/') ? pathname : `/${pathname}`;
  const normalizedPath = leadingSlashPath === '/' ? '/' : leadingSlashPath.replace(/\/+$/, '');
  return new URL(normalizedPath, `${origin}/`).toString();
}

function configuredPublicOrigin(): string | null {
  const raw = import.meta.env.VITE_PUBLIC_SITE_ORIGIN?.trim();
  if (!raw) return null;

  try {
    const url = new URL(raw);
    const hostname = url.hostname.toLowerCase();
    const localHost = hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1' || hostname.endsWith('.local');
    const bareOrigin = url.pathname === '/' && !url.search && !url.hash && !url.username && !url.password;

    if (url.protocol !== 'https:' || localHost || !bareOrigin) return null;
    return url.origin;
  } catch {
    return null;
  }
}
