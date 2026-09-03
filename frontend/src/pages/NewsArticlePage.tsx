import { useEffect, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';

import { ReferenceInnerPage, ReferenceNotice, ReferencePanel } from '../components/ReferenceInnerPage';
import { PublicContentApiError, getPublicNews, type PublicNewsArticle } from '../publicContent/publicContentApi';
import { applyDocumentSeo, siteTitle } from '../seo/seo';

const DATE = new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' });

export function NewsArticlePage() {
  const { slug } = useParams();
  const location = useLocation();
  const [article, setArticle] = useState<PublicNewsArticle | null>(null);
  const [state, setState] = useState<'loading' | 'ready' | 'notfound' | 'error'>('loading');
  const hero = getHeroState(state, article);

  useEffect(() => {
    const controller = new AbortController();
    setArticle(null);
    setState('loading');

    if (!slug) {
      setState('notfound');
      return () => controller.abort();
    }

    void getPublicNews(slug, controller.signal)
      .then((value) => {
        setArticle(value);
        setState('ready');
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') {
          return;
        }
        if (error instanceof PublicContentApiError && error.status === 404) {
          setState('notfound');
          return;
        }
        setState('error');
      });

    return () => controller.abort();
  }, [slug]);

  useEffect(() => {
    const publishedArticle = state === 'ready' && article?.slug === slug ? article : null;
    if (publishedArticle) {
      applyDocumentSeo({
        title: siteTitle(publishedArticle.title),
        description: publishedArticle.excerpt.trim() || publishedArticle.title,
        pathname: location.pathname,
        indexable: true,
      });
      return;
    }

    applyDocumentSeo({
      title: siteTitle(hero.title),
      description: hero.lead,
      pathname: location.pathname,
      indexable: false,
    });
  }, [article, hero.lead, hero.title, location.pathname, slug, state]);

  return (
    <ReferenceInnerPage eyebrow="Новости" title={hero.title} lead={hero.lead}>
      {state === 'loading' ? (
        <ReferenceNotice title="Загрузка материала">Материал загружается.</ReferenceNotice>
      ) : null}

      {state === 'error' ? (
        <ReferenceNotice title="Материал временно недоступен">
          Материал не удалось загрузить. Попробуйте открыть страницу позже.
        </ReferenceNotice>
      ) : null}

      {state === 'notfound' ? (
        <ReferenceNotice title="Материал не опубликован">
          Запрошенный материал не опубликован. На странице не показываются демонстрационные или предположительные тексты.
        </ReferenceNotice>
      ) : null}

      {state === 'ready' && article ? (
        <ReferencePanel className="mx-auto w-full max-w-4xl">
          <article className="space-y-7">
            {article.published_at ? (
              <time className="text-xs uppercase tracking-[0.14em] text-brand-reference-red" dateTime={article.published_at}>
                {DATE.format(new Date(article.published_at))}
              </time>
            ) : null}
            {article.image_url ? (
              <img
                src={article.image_url}
                alt={`Иллюстрация к новости «${article.title}»`}
                className="w-full rounded-[5px] border border-brand-reference-line/25 bg-brand-reference-panelDeep object-cover"
              />
            ) : null}
            <div className="space-y-5 text-[15px] font-light leading-8 text-brand-reference-muted">
              {renderParagraphs(article.body)}
            </div>
            <Link
              className="inline-block border-b border-brand-reference-red pb-1 text-sm font-semibold uppercase tracking-[0.08em] text-brand-reference-text transition-colors hover:text-white"
              to="/novosti"
            >
              Вернуться к новостям
            </Link>
          </article>
        </ReferencePanel>
      ) : null}
    </ReferenceInnerPage>
  );
}

function renderParagraphs(value: string) {
  return value
    .trim()
    .split(/\n\s*\n/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)
    .map((paragraph, index) => (
      <p key={`news-paragraph-${index}`} className="whitespace-pre-line">
        {paragraph}
      </p>
    ));
}

function getHeroState(
  state: 'loading' | 'ready' | 'notfound' | 'error',
  article: PublicNewsArticle | null,
) {
  switch (state) {
    case 'loading':
      return {
        title: 'Загрузка материала',
        lead: 'Материал загружается. Пожалуйста, подождите.',
      };
    case 'ready':
      return {
        title: article?.title ?? 'Новости',
        lead: article?.excerpt ?? 'Опубликованный новостной материал.',
      };
    case 'notfound':
      return {
        title: 'Материал не опубликован',
        lead: 'Запрошенный материал не опубликован или еще не утвержден.',
      };
    case 'error':
      return {
        title: 'Материал временно недоступен',
        lead: 'Не удалось загрузить материал. Попробуйте открыть страницу позже.',
      };
  }
}
