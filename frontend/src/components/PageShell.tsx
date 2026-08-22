import { Outlet, ScrollRestoration, useMatches } from 'react-router-dom';
import type { SeoMeta } from '../routes';
import { SiteFooter } from './SiteFooter';
import { SiteHeader } from './SiteHeader';

export function PageShell() {
  const matches = useMatches();
  const meta = [...matches].reverse().find((match) => match.handle)?.handle as SeoMeta | undefined;

  if (meta) {
    document.title = meta.title;
    setMetaDescription(meta.description);
  }

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

function setMetaDescription(description: string) {
  let element = document.querySelector<HTMLMetaElement>('meta[name="description"]');
  if (!element) {
    element = document.createElement('meta');
    element.name = 'description';
    document.head.appendChild(element);
  }
  element.content = description;
}
