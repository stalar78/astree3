import { useEffect, useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';

import { ReferenceLayout } from '../components/ReferenceLayout';
import { getPublicPage, type PublicPage } from '../publicContent/publicContentApi';

type HomeBlock = {
  eyebrow: string;
  title: string;
  text: string;
  imageUrl?: string;
  imagePosition?: string;
  href?: string;
};

const DEFAULT_BLOCKS: HomeBlock[] = [
  {
    eyebrow: 'Астрея №3',
    title: 'Добро пожаловать в достопочтенную ложу «Астрея» № 3 на Востоке Санкт-Петербурга',
    text:
      'Единственная регулярная Великая Ложа, действующая на территории России, признанная регулярными Великими Ложами стран мира. Вновь учрежденная в 1995 году, Великая Ложа России неукоснительно хранит древние традиции Ордена и содействует распространению масонского света на территории России и СНГ.',
    imageUrl: '/media/home/home-welcome.webp',
    imagePosition: 'center 44%',
  },
  {
    eyebrow: 'События',
    title: 'Новости ложи',
    text: 'Официальные сообщения появятся здесь после публикации через административную панель.',
    imageUrl: '/media/home/home-events.webp',
    imagePosition: 'center 44%',
    href: '/novosti',
  },
  {
    eyebrow: 'Материалы',
    title: 'Публикации и медиа',
    text: 'Разделы сайта подготовлены для утвержденных материалов, фотографий и видеопубликаций.',
    imageUrl: '/media/home/home-media.webp',
    href: '/materialy',
  },
];

const HOME_KEYS = ['home_1', 'home_2', 'home_3'] as const;

export function HomePage() {
  const [blocks, setBlocks] = useState<HomeBlock[]>(DEFAULT_BLOCKS);

  useEffect(() => {
    const controller = new AbortController();
    void Promise.all(HOME_KEYS.map((key) => getPublicPage(key, controller.signal)))
      .then((pages) => setBlocks(pages.map((page, index) => parseHomeBlock(page, DEFAULT_BLOCKS[index]))))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        setBlocks(DEFAULT_BLOCKS);
      });
    return () => controller.abort();
  }, []);

  return (
    <ReferenceLayout>
      <div className="space-y-6 sm:space-y-8 lg:space-y-7">
        {blocks.map((block, index) => (
          <ReferenceCard key={HOME_KEYS[index]} primary={index === 0} {...block} />
        ))}
      </div>
    </ReferenceLayout>
  );
}

function parseHomeBlock(page: PublicPage, fallback: HomeBlock): HomeBlock {
  try {
    const parsed = JSON.parse(page.content) as unknown;
    if (!parsed || typeof parsed !== 'object') return { ...fallback, title: page.title };
    const values = parsed as Record<string, unknown>;
    return {
      eyebrow: typeof values.eyebrow === 'string' && values.eyebrow.trim() ? values.eyebrow : fallback.eyebrow,
      title: page.title || fallback.title,
      text: typeof values.text === 'string' && values.text.trim() ? values.text : fallback.text,
      imageUrl: typeof values.image_url === 'string' && values.image_url.trim() ? values.image_url : fallback.imageUrl,
      imagePosition: fallback.imagePosition,
      href: typeof values.href === 'string' && values.href.trim() ? values.href : undefined,
    };
  } catch {
    return { ...fallback, title: page.title || fallback.title };
  }
}

function ReferenceCard({
  eyebrow,
  title,
  text,
  imageUrl,
  imagePosition,
  href,
  primary = false,
}: HomeBlock & { primary?: boolean }) {
  const Heading = primary ? 'h1' : 'h2';
  const body = (
    <article className="rounded-[6px] border border-brand-reference-line/30 bg-brand-reference-panel px-5 py-6 shadow-referenceCard transition-colors hover:border-brand-reference-line/45 sm:px-6 sm:py-7 lg:px-7 lg:py-7">
      <div className="grid gap-5 md:grid-cols-[35%_1fr] md:items-start md:gap-5">
        <div className="overflow-hidden rounded-[5px] border border-brand-reference-line/20 bg-brand-reference-panelDeep">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt=""
              className="aspect-[16/10] w-full object-cover sm:aspect-[1.45/1]"
              style={imagePosition ? { objectPosition: imagePosition } : undefined}
            />
          ) : (
            <div className="aspect-[16/10] bg-[#0A0D13] sm:aspect-[1.45/1]" aria-hidden="true" />
          )}
        </div>

        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.12em] text-brand-reference-muted/55">{eyebrow}</p>
          <Heading className="mt-2 break-words font-referenceHeading text-[clamp(1.45rem,6vw,1.85rem)] font-medium leading-[1.12] text-brand-reference-text md:text-[clamp(1.28rem,1.55vw,1.58rem)]">
            {title}
          </Heading>
          <div className="my-4 h-px bg-brand-reference-line/75" />
          <p className="hidden text-[15px] font-light leading-[1.4] text-brand-reference-muted md:block lg:text-sm lg:leading-6">{text}</p>
        </div>
      </div>
      <p className="mt-4 text-[15px] font-light leading-[1.5] text-brand-reference-muted sm:mt-5 sm:leading-[1.42] lg:text-sm lg:leading-6">{text}</p>
    </article>
  );

  return wrapCardLink(body, href);
}

function wrapCardLink(body: ReactNode, href?: string) {
  if (!href) return body;
  if (href.startsWith('/')) {
    return (
      <Link to={href} className="block focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-reference-line">
        {body}
      </Link>
    );
  }
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="block focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-reference-line"
    >
      {body}
    </a>
  );
}
