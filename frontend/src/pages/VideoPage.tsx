import { useEffect, useState } from 'react';

import { ReferenceInnerPage, ReferenceNotice, ReferencePanel } from '../components/ReferenceInnerPage';
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
    <ReferenceInnerPage
      eyebrow="Видеоматериалы"
      title="Видео"
      lead="Раздел предназначен для утвержденных внешних ссылок, преимущественно RuTube."
    >
      {state === 'loading' ? (
        <ReferenceNotice title="Загрузка видео">Раздел загружается.</ReferenceNotice>
      ) : null}

      {state === 'error' ? (
        <ReferenceNotice title="Раздел временно недоступен">
          Видео не удалось загрузить. Попробуйте открыть раздел позднее.
        </ReferenceNotice>
      ) : null}

      {state === 'ready' && videos.length === 0 ? (
        <ReferenceNotice title="Видео пока не опубликованы">
          Утвержденные видео еще не опубликованы. Раздел сохранен как официальный экран без демонстрационных материалов.
        </ReferenceNotice>
      ) : null}

      {state === 'ready' && videos.length > 0 ? (
        <div className="space-y-8">
          {videos.map((video) => (
            <ReferencePanel key={video.id}>
              <article className="space-y-6">
                <div className="space-y-3">
                  {video.published_at ? (
                    <time className="text-xs uppercase tracking-[0.14em] text-brand-reference-red" dateTime={video.published_at}>
                      {DATE.format(new Date(video.published_at))}
                    </time>
                  ) : null}
                  <h2 className="font-referenceHeading text-[clamp(1.75rem,2.4vw,2.4rem)] font-normal leading-tight text-brand-reference-text">
                    {video.title}
                  </h2>
                  <div className="h-px bg-brand-reference-line/65" />
                  <p className="max-w-4xl text-[15px] font-light leading-7 text-brand-reference-muted">{video.description}</p>
                </div>

                <div className="overflow-hidden rounded-[5px] border border-brand-reference-line/30 bg-brand-reference-panelDeep shadow-referenceCard">
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
                    className="inline-flex border-b border-brand-reference-red pb-1 text-sm font-semibold uppercase tracking-[0.08em] text-brand-reference-text transition-colors hover:text-white"
                  >
                    Открыть источник
                  </a>
                ) : null}
              </article>
            </ReferencePanel>
          ))}
        </div>
      ) : null}
    </ReferenceInnerPage>
  );
}
