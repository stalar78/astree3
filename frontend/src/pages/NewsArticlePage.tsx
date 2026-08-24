import { useEffect, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';

import { EditorialNote } from '../components/EditorialNote';
import { InternalHero } from '../components/InternalHero';
import { Section } from '../components/Section';
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
    <>
      <InternalHero eyebrow="Новости" title={hero.title} lead={hero.lead} />
      <Section>
        <div className="mx-auto max-w-4xl">
          {state === 'loading' ? <EditorialNote title="Загрузка материала">Материал загружается.</EditorialNote> : null}

          {state === 'error' ? (
            <EditorialNote title="Материал временно недоступен">Материал не удалось загрузить. Попробуйте открыть страницу позже.</EditorialNote>
          ) : null}

          {state === 'notfound' ? (
            <EditorialNote title="Материал не опубликован">
              Запрошенный материал не опубликован. На странице не показываются демонстрационные или предположительные тексты.
            </EditorialNote>
          ) : null}

          {state === 'ready' && article ? (
            <article className="space-y-8">
              {article.published_at ? (
                <time className="text-sm uppercase tracking-[0.12em] text-brand-red" dateTime={article.published_at}>
                  {DATE.format(new Date(article.published_at))}
                </time>
              ) : null}
              {article.image_url ? (
                <img src={article.image_url} alt={`Иллюстрация к новости «${article.title}»`} className="w-full border border-brand-gray10/20 bg-brand-paperAlt object-cover" />
              ) : null}
              <div className="space-y-5 text-base leading-8 text-brand-ink/80">
                {renderParagraphs(article.body)}
              </div>
              <Link className="inline-block border-b border-brand-red pb-1 text-sm font-semibold uppercase text-brand-black" to="/novosti">
                Вернуться к новостям
              </Link>
            </article>
          ) : null}
        </div>
      </Section>
    </>
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
