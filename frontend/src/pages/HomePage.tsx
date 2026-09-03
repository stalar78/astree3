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
      <div className="space-y-6 sm:space-y-8 lg:space-y-10">
        <ReferenceCard
          primary
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
  primary = false,
}: {
  eyebrow: string;
  title: string;
  text: string;
  imageUrl?: string;
  href?: string;
  primary?: boolean;
}) {
  const Heading = primary ? 'h1' : 'h2';
  const body = (
    <article className="rounded-[6px] border border-brand-reference-line/30 bg-brand-reference-panel px-5 py-6 shadow-referenceCard transition-colors hover:border-brand-reference-line/45 sm:px-6 sm:py-7 lg:px-8 lg:py-8">
      <div className="grid gap-5 md:grid-cols-[36%_1fr] md:items-start md:gap-6">
        <div className="overflow-hidden rounded-[5px] border border-brand-reference-line/20 bg-brand-reference-panelDeep">
          {imageUrl ? (
            <img src={imageUrl} alt="" className="aspect-[16/10] w-full object-cover sm:aspect-[1.45/1]" />
          ) : (
            <div className="aspect-[16/10] bg-[#0A0D13] sm:aspect-[1.45/1]" aria-hidden="true" />
          )}
        </div>

        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.12em] text-brand-reference-muted/55">{eyebrow}</p>
          <Heading className="mt-2 break-words text-[clamp(1.45rem,6vw,1.85rem)] font-light leading-[1.12] text-brand-reference-text md:text-[clamp(1.35rem,1.85vw,1.85rem)]">{title}</Heading>
          <div className="my-5 h-px bg-brand-reference-line/75" />
          <p className="hidden text-[15px] font-light leading-[1.4] text-brand-reference-muted md:block">{text}</p>
        </div>
      </div>
      <p className="mt-4 text-[15px] font-light leading-[1.5] text-brand-reference-muted sm:mt-5 sm:leading-[1.42]">{text}</p>
    </article>
  );

  return href ? (
    <Link to={href} className="block focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-reference-line">
      {body}
    </Link>
  ) : body;
}
