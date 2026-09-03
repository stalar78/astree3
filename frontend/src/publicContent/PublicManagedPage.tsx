import { useEffect, type ReactNode } from 'react';
import { useLocation } from 'react-router-dom';

import { ReferenceInnerPage, ReferenceNotice, ReferencePanel } from '../components/ReferenceInnerPage';
import { applyDocumentSeo, seoDescriptionFromText, siteTitle } from '../seo/seo';
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
  afterContent?: ReactNode;
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
  afterContent,
  children,
}: PublicManagedPageFrameProps) {
  const location = useLocation();
  const { status, page, retry } = usePublicManagedPage(pageKey);
  const readyPage = status === 'ready' && page ? page : null;
  const heroTitle = readyPage?.title ?? fallbackTitle;

  useEffect(() => {
    const description = readyPage
      ? seoDescriptionFromText(readyPage.content, readyPage.title)
      : status === 'error'
        ? errorMessage
        : status === 'not_found'
          ? notFoundMessage
          : loadingMessage;

    applyDocumentSeo({
      title: siteTitle(heroTitle),
      description,
      pathname: location.pathname,
      indexable: Boolean(readyPage),
    });
  }, [errorMessage, heroTitle, loadingMessage, location.pathname, notFoundMessage, readyPage, status]);

  return (
    <ReferenceInnerPage eyebrow={eyebrow} title={heroTitle}>
      <div className={`mx-auto w-full ${bodyWidthClassName}`}>
        {status === 'loading' ? <PublicManagedPageState title={loadingTitle} message={loadingMessage} /> : null}
        {status === 'not_found' ? <PublicManagedPageState title={notFoundTitle} message={notFoundMessage} /> : null}
        {status === 'error' ? (
          <PublicManagedPageState title={errorTitle} message={errorMessage} retryLabel={retryLabel} onRetry={retry} />
        ) : null}
        {readyPage ? <ReferencePanel>{children(readyPage)}</ReferencePanel> : null}
      </div>
      {afterContent}
    </ReferenceInnerPage>
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
    <ReferenceNotice
      title={title}
      action={
        onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center justify-center rounded-[5px] border border-brand-reference-red px-5 py-3 text-sm font-semibold uppercase tracking-[0.08em] text-brand-reference-text transition hover:bg-brand-reference-red focus:outline focus:outline-2 focus:outline-offset-4 focus:outline-brand-reference-red"
          >
            {retryLabel}
          </button>
        ) : undefined
      }
    >
      {message}
    </ReferenceNotice>
  );
}

type PublicPageBodyProps = {
  page: PublicPage;
};

export function PublicPageBody({ page }: PublicPageBodyProps) {
  return <div className="whitespace-pre-wrap text-[15px] font-light leading-8 text-brand-reference-muted">{page.content}</div>;
}
