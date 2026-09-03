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
    <div className="public-redesign min-h-screen bg-brand-reference-canvas text-brand-reference-text">
      <SiteHeader />
      <main id="content" className="min-h-[45vh]">
        <Outlet />
      </main>
      <SiteFooter />
      <ScrollRestoration />
    </div>
  );
}
