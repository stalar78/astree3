import { useEffect, useState } from 'react';

import { EditorialNote } from '../components/EditorialNote';
import { InternalHero } from '../components/InternalHero';
import { Section } from '../components/Section';
import { listPublicVideos, type PublicVideo } from '../publicContent/publicContentApi';

const DATE = new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' });

export function VideoPage() {
  const [videos, setVideos] = useState<PublicVideo[]>([]);
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading');

  useEffect(() => {
    const controller = new AbortController();
    setState('loading');

    void listPublicVideos(controller.signal)
      .then((items) => {
        setVideos(items);
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
      <InternalHero eyebrow="Видеоматериалы" title="Видео" lead="Раздел предназначен для утвержденных внешних ссылок, преимущественно RuTube." />
      <Section>
        <div className="mx-auto max-w-5xl">
          {state === 'loading' ? (
            <EditorialNote title="Загрузка видео">Раздел загружается.</EditorialNote>
          ) : null}

          {state === 'error' ? (
            <EditorialNote title="Раздел временно недоступен">Видео не удалось загрузить. Попробуйте открыть раздел позднее.</EditorialNote>
          ) : null}

          {state === 'ready' && videos.length === 0 ? (
            <EditorialNote title="Видео пока не опубликованы">
              Утвержденные видео еще не опубликованы. Раздел сохранен как официальный экран без демонстрационных материалов.
            </EditorialNote>
          ) : null}

          {state === 'ready' && videos.length > 0 ? (
            <div className="space-y-10">
              {videos.map((video) => (
                <article key={video.id} className="space-y-5 border-b border-brand-gray10/20 pb-10 last:border-b-0 last:pb-0">
                  <div className="space-y-3">
                    {video.published_at ? (
                      <time className="text-sm uppercase tracking-[0.12em] text-brand-red" dateTime={video.published_at}>
                        {DATE.format(new Date(video.published_at))}
                      </time>
                    ) : null}
                    <h2 className="font-display text-4xl leading-tight text-brand-ink">{video.title}</h2>
                    <p className="max-w-4xl text-base leading-8 text-brand-ink/75">{video.description}</p>
                  </div>

                  <div className="overflow-hidden rounded-3xl border border-brand-gray10/20 bg-brand-black shadow-formal">
                    <div className="relative aspect-video">
                      <iframe
                        title={`Видео: ${video.title}`}
                        src={video.embed_url}
                        loading="lazy"
                        allowFullScreen
                        referrerPolicy="strict-origin-when-cross-origin"
                        className="absolute inset-0 h-full w-full"
                      />
                    </div>
                  </div>

                  {video.source_url ? (
                    <a
                      href={video.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex border-b border-brand-red pb-1 text-sm font-semibold uppercase text-brand-black transition hover:text-brand-red"
                    >
                      Открыть источник
                    </a>
                  ) : null}
                </article>
              ))}
            </div>
          ) : null}
        </div>
      </Section>
    </>
  );
}
