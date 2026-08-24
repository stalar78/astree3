import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { EditorialNote } from '../components/EditorialNote';
import { InternalHero } from '../components/InternalHero';
import { Section } from '../components/Section';
import { listPublicNews, type PublicNewsListItem } from '../publicContent/publicContentApi';

const DATE = new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' });

export function NewsPage() {
  const [items, setItems] = useState<PublicNewsListItem[]>([]);
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading');

  useEffect(() => {
    const controller = new AbortController();
    setState('loading');

    void listPublicNews(controller.signal)
      .then((news) => {
        setItems(news);
        setState('ready');
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') {
          return;
        }
        setState('error');
      });

    return () => controller.abort();
  }, []);

  return (
    <>
      <InternalHero eyebrow="Архив" title="Новости" lead="Новостной раздел подготовлен для утвержденных публикаций." />
      <Section>
        <div className="mx-auto max-w-5xl">
          {state === 'loading' ? (
            <EditorialNote title="Загрузка новостей">Раздел загружается.</EditorialNote>
          ) : null}

          {state === 'error' ? (
            <EditorialNote title="Раздел временно недоступен">Новости не удалось загрузить. Попробуйте открыть раздел позднее.</EditorialNote>
          ) : null}

          {state === 'ready' && items.length === 0 ? (
            <EditorialNote title="Новостей пока нет">
              Утвержденные новости еще не опубликованы. Раздел сохранен как официальный архивный экран без демонстрационных материалов.
            </EditorialNote>
          ) : null}

          {state === 'ready' && items.length > 0 ? (
            <div className="space-y-8">
              {items.map((item) => (
                <article key={item.slug} className="grid gap-6 border-b border-brand-gray10/20 pb-8 last:border-b-0 lg:grid-cols-[220px_1fr]">
                  {item.image_url ? (
                    <Link to={`/novosti/${item.slug}`} className="block overflow-hidden border border-brand-gray10/20 bg-brand-paperAlt">
                      <img src={item.image_url} alt={`Иллюстрация к новости «${item.title}»`} className="aspect-[4/3] w-full object-cover" />
                    </Link>
                  ) : null}
                  <div className={item.image_url ? '' : 'lg:col-span-2'}>
                    {item.published_at ? (
                      <time className="text-sm uppercase tracking-[0.12em] text-brand-red" dateTime={item.published_at}>
                        {DATE.format(new Date(item.published_at))}
                      </time>
                    ) : null}
                    <h2 className="mt-3 font-display text-4xl leading-tight text-brand-ink">
                      <Link to={`/novosti/${item.slug}`} className="transition hover:text-brand-red">
                        {item.title}
                      </Link>
                    </h2>
                    <p className="mt-4 text-base leading-8 text-brand-ink/75">{item.excerpt}</p>
                    <Link className="mt-5 inline-block border-b border-brand-red pb-1 text-sm font-semibold uppercase text-brand-black" to={`/novosti/${item.slug}`}>
                      Читать материал
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          ) : null}
        </div>
      </Section>
    </>
  );
}
