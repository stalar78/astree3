import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { ReferenceLayout } from '../components/ReferenceLayout';
import { listPublicNews, type PublicNewsListItem } from '../publicContent/publicContentApi';

const WELCOME_TEXT =
  'Единственная регулярная Великая Ложа, действующая на территории России, признанная регулярными Великими Ложами стран мира. Вновь учрежденная в 1995 году, Великая Ложа России неукоснительно хранит древние традиции Ордена и содействует распространению масонского света на территории России и СНГ.';

export function HomePage() {
  const [news, setNews] = useState<PublicNewsListItem[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    void listPublicNews(controller.signal)
      .then((items) => setNews(items.slice(0, 2)))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        setNews([]);
      });
    return () => controller.abort();
  }, []);

  return (
    <ReferenceLayout>
      <div className="space-y-10">
        <ReferenceCard
          eyebrow="Астрея №3"
          title={'Добро пожаловать в достопочтенную ложу «Астрея» № 3 на Востоке Санкт-Петербурга'}
          text={WELCOME_TEXT}
        />

        {news.length > 0
          ? news.map((item) => (
              <ReferenceCard
                key={item.slug}
                eyebrow="События"
                title={item.title}
                text={item.excerpt}
                imageUrl={item.image_url ?? undefined}
                href={`/novosti/${item.slug}`}
              />
            ))
          : (
            <>
              <ReferenceCard
                eyebrow="События"
                title="Новости ложи"
                text="Официальные сообщения появятся здесь после публикации через административную панель."
                href="/novosti"
              />
              <ReferenceCard
                eyebrow="Материалы"
                title="Публикации и медиа"
                text="Разделы сайта подготовлены для утвержденных материалов, фотографий и видеопубликаций."
                href="/video"
              />
            </>
          )}
      </div>
    </ReferenceLayout>
  );
}

function ReferenceCard({
  eyebrow,
  title,
  text,
  imageUrl,
  href,
}: {
  eyebrow: string;
  title: string;
  text: string;
  imageUrl?: string;
  href?: string;
}) {
  const body = (
    <article className="rounded-md border border-white/10 bg-brand-reference-panel px-6 py-7 shadow-referenceCard transition-colors hover:border-white/15 lg:px-8 lg:py-8">
      <div className="grid gap-6 md:grid-cols-[36%_1fr] md:items-start">
        <div className="overflow-hidden rounded-sm border border-white/10 bg-brand-reference-panelDeep">
          {imageUrl ? (
            <img src={imageUrl} alt="" className="aspect-[1.45/1] w-full object-cover" />
          ) : (
            <div className="flex aspect-[1.45/1] items-center justify-center px-6 text-center text-xs uppercase tracking-[0.16em] text-brand-reference-muted/45">
              Фото будет предоставлено заказчиком
            </div>
          )}
        </div>

        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.12em] text-brand-reference-muted/60">{eyebrow}</p>
          <h1 className="mt-2 text-[clamp(1.45rem,2.1vw,2rem)] font-light leading-[1.08] text-brand-reference-text">{title}</h1>
          <div className="my-5 h-px bg-brand-reference-line/80" />
          <p className="text-[15px] font-light leading-[1.35] text-brand-reference-muted">{text}</p>
        </div>
      </div>
      <p className="mt-5 text-[15px] font-light leading-[1.4] text-brand-reference-muted">{text}</p>
    </article>
  );

  return href ? (
    <Link to={href} className="block focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-reference-line">
      {body}
    </Link>
  ) : body;
}
