import type { ReactNode } from 'react';

import { EditorialNote } from '../components/EditorialNote';
import { InternalHero } from '../components/InternalHero';
import { Section } from '../components/Section';
import type { PublicPage } from './publicContentApi';
import { usePublicManagedPage } from './usePublicManagedPage';

type PublicManagedPageFrameProps = {
  eyebrow: string;
  fallbackTitle: string;
  pageKey: string;
  loadingTitle: string;
  loadingMessage: string;
  notFoundTitle: string;
  notFoundMessage: string;
  errorTitle: string;
  errorMessage: string;
  retryLabel: string;
  bodyWidthClassName?: string;
  children: (page: PublicPage) => ReactNode;
};

export function PublicManagedPageFrame({
  eyebrow,
  fallbackTitle,
  pageKey,
  loadingTitle,
  loadingMessage,
  notFoundTitle,
  notFoundMessage,
  errorTitle,
  errorMessage,
  retryLabel,
  bodyWidthClassName = 'max-w-3xl',
  children,
}: PublicManagedPageFrameProps) {
  const { status, page, retry } = usePublicManagedPage(pageKey);
  const heroTitle = status === 'ready' && page ? page.title : fallbackTitle;

  return (
    <>
      <InternalHero eyebrow={eyebrow} title={heroTitle} />
      <Section>
        <div className={`mx-auto ${bodyWidthClassName}`}>
          {status === 'loading' ? <PublicManagedPageState title={loadingTitle} message={loadingMessage} /> : null}
          {status === 'not_found' ? <PublicManagedPageState title={notFoundTitle} message={notFoundMessage} /> : null}
          {status === 'error' ? (
            <PublicManagedPageState title={errorTitle} message={errorMessage} retryLabel={retryLabel} onRetry={retry} />
          ) : null}
          {status === 'ready' && page ? children(page) : null}
        </div>
      </Section>
    </>
  );
}

type PublicManagedPageStateProps = {
  title: string;
  message: string;
  retryLabel?: string;
  onRetry?: () => void;
};

function PublicManagedPageState({ title, message, retryLabel, onRetry }: PublicManagedPageStateProps) {
  return (
    <div className="space-y-6">
      <EditorialNote title={title}>{message}</EditorialNote>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-6 inline-flex items-center justify-center border border-brand-red px-5 py-3 text-sm font-semibold uppercase tracking-[0.08em] text-brand-red transition hover:bg-brand-red hover:text-white focus:outline focus:outline-2 focus:outline-offset-4 focus:outline-brand-red"
        >
          {retryLabel}
        </button>
      ) : null}
    </div>
  );
}

type PublicPageBodyProps = {
  page: PublicPage;
};

export function PublicPageBody({ page }: PublicPageBodyProps) {
  return <div className="whitespace-pre-wrap text-base leading-8 text-brand-ink/75">{page.content}</div>;
}
