import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { ReferenceInnerPage, ReferenceNotice, ReferencePanel } from '../components/ReferenceInnerPage';
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
    <ReferenceInnerPage eyebrow="Архив" title="Новости" lead="Новостной раздел подготовлен для утвержденных публикаций.">
      {state === 'loading' ? (
        <ReferenceNotice title="Загрузка новостей">Раздел загружается.</ReferenceNotice>
      ) : null}

      {state === 'error' ? (
        <ReferenceNotice title="Раздел временно недоступен">
          Новости не удалось загрузить. Попробуйте открыть раздел позднее.
        </ReferenceNotice>
      ) : null}

      {state === 'ready' && items.length === 0 ? (
        <ReferenceNotice title="Новостей пока нет">
          Утвержденные новости еще не опубликованы. Раздел сохранен как официальный архивный экран без демонстрационных материалов.
        </ReferenceNotice>
      ) : null}

      {state === 'ready' && items.length > 0 ? (
        <div className="space-y-8">
          {items.map((item) => (
            <ReferencePanel key={item.slug}>
              <article className="grid gap-6 lg:grid-cols-[220px_1fr]">
                {item.image_url ? (
                  <Link
                    to={`/novosti/${item.slug}`}
                    className="block overflow-hidden rounded-[5px] border border-brand-reference-line/25 bg-brand-reference-panelDeep"
                  >
                    <img src={item.image_url} alt={`Иллюстрация к новости «${item.title}»`} className="aspect-[4/3] w-full object-cover" />
                  </Link>
                ) : null}
                <div className={item.image_url ? '' : 'lg:col-span-2'}>
                  {item.published_at ? (
                    <time className="text-xs uppercase tracking-[0.14em] text-brand-reference-red" dateTime={item.published_at}>
                      {DATE.format(new Date(item.published_at))}
                    </time>
                  ) : null}
                  <h2 className="mt-3 font-referenceHeading text-[clamp(1.75rem,2.4vw,2.4rem)] font-medium leading-tight text-brand-reference-text">
                    <Link to={`/novosti/${item.slug}`} className="transition-colors hover:text-white">
                      {item.title}
                    </Link>
                  </h2>
                  <div className="my-4 h-px bg-brand-reference-line/65" />
                  <p className="text-[15px] font-light leading-7 text-brand-reference-muted">{item.excerpt}</p>
                  <Link
                    className="mt-5 inline-block border-b border-brand-reference-red pb-1 text-sm font-semibold uppercase tracking-[0.08em] text-brand-reference-text transition-colors hover:text-white"
                    to={`/novosti/${item.slug}`}
                  >
                    Читать материал
                  </Link>
                </div>
              </article>
            </ReferencePanel>
          ))}
        </div>
      ) : null}
    </ReferenceInnerPage>
  );
}
