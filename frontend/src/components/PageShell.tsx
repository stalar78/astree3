import { useEffect } from 'react';
import { Outlet, ScrollRestoration, useLocation, useMatches } from 'react-router-dom';
import type { SeoMeta } from '../routes';
import { applyDocumentSeo } from '../seo/seo';
import { SiteFooter } from './SiteFooter';
import { SiteHeader } from './SiteHeader';

export function PageShell() {
  const location = useLocation();
  const matches = useMatches();
  const meta = [...matches].reverse().find((match) => match.handle)?.handle as SeoMeta | undefined;

  useEffect(() => {
    if (!meta) return;
    applyDocumentSeo({
      title: meta.title,
      description: meta.description,
      pathname: location.pathname,
      indexable: meta.indexable !== false,
    });
  }, [location.pathname, meta]);

  return (
    <div className="min-h-screen bg-brand-paper text-brand-ink">
      <SiteHeader />
      <main id="content">
        <Outlet />
      </main>
      <SiteFooter />
      <ScrollRestoration />
    </div>
  );
}
