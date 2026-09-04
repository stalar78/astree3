import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

import { ReferenceInnerPage, ReferenceNotice, ReferencePanel } from '../components/ReferenceInnerPage';
import { isHostingEdition } from '../config/edition';
import {
  listPublicMaterials,
  type PublicMaterial,
  type PublicMaterialType,
} from '../publicContent/publicContentApi';
import { usePublicManagedPage } from '../publicContent/usePublicManagedPage';
import { applyDocumentSeo, seoDescriptionFromText, siteTitle } from '../seo/seo';

const FALLBACK_TITLE = 'Материалы';
const FALLBACK_LEAD = 'Публикации, новости и видеоматериалы Д.·. Л.·. «Астрея» №3.';
const DATE = new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' });

const MATERIAL_GROUPS: Array<{
  type: PublicMaterialType;
  eyebrow: string;
  title: string;
}> = [
  { type: 'book', eyebrow: 'Библиотека', title: 'Книги' },
  { type: 'video', eyebrow: 'Медиа', title: 'Видео' },
  { type: 'audio', eyebrow: 'Аудио', title: 'Аудио и подкасты' },
  { type: 'article', eyebrow: 'Чтение', title: 'Статьи' },
];

export function MaterialsPage() {
  const location = useLocation();
  const { status, page } = usePublicManagedPage('materials');
  const readyPage = status === 'ready' && page ? page : null;
  const title = readyPage?.title ?? FALLBACK_TITLE;
  const description = readyPage ? seoDescriptionFromText(readyPage.content, FALLBACK_LEAD) : FALLBACK_LEAD;
  const [materials, setMaterials] = useState<PublicMaterial[]>([]);
  const [materialsState, setMaterialsState] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');

  useEffect(() => {
    applyDocumentSeo({
      title: siteTitle(title),
      description,
      pathname: location.pathname,
      indexable: true,
    });
  }, [description, location.pathname, title]);

  useEffect(() => {
    if (!isHostingEdition) return;

    const controller = new AbortController();
    setMaterialsState('loading');

    void listPublicMaterials(controller.signal)
      .then((items) => {
        setMaterials(items);
        setMaterialsState('ready');
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        setMaterials([]);
        setMaterialsState('error');
      });

    return () => controller.abort();
  }, []);

  return (
    <ReferenceInnerPage eyebrow="Материалы" title={title} lead={readyPage ? undefined : FALLBACK_LEAD}>
      <div className="space-y-6">
        {readyPage ? (
          <ReferencePanel>
            <div className="whitespace-pre-wrap text-[15px] font-light leading-8 text-brand-reference-muted">{readyPage.content}</div>
          </ReferencePanel>
        ) : null}

        {isHostingEdition ? <HostingMaterials state={materialsState} materials={materials} /> : null}

        <div className="grid gap-6 md:grid-cols-2">
          <MaterialLink
            to="/novosti"
            eyebrow="Публикации"
            title="Новости и события"
            text="Официальные сообщения и опубликованные материалы ложи."
          />
          <MaterialLink
            to="/video"
            eyebrow="Медиа"
            title="Видео"
            text="Опубликованные видеоматериалы и ссылки на утвержденные внешние источники."
          />
        </div>
      </div>
    </ReferenceInnerPage>
  );
}

function HostingMaterials({ state, materials }: { state: 'idle' | 'loading' | 'ready' | 'error'; materials: PublicMaterial[] }) {
  if (state === 'loading') {
    return <ReferenceNotice title="Загрузка материалов">Подборка загружается.</ReferenceNotice>;
  }

  if (state === 'error') {
    return (
      <ReferenceNotice title="Материалы временно недоступны">
        Не удалось загрузить опубликованную подборку. Попробуйте открыть раздел позднее.
      </ReferenceNotice>
    );
  }

  if (state === 'ready' && materials.length === 0) {
    return (
      <ReferenceNotice title="Подборка пока не опубликована">
        Рекомендованные книги, аудио, видео и статьи появятся здесь после публикации в редакторе.
      </ReferenceNotice>
    );
  }

  if (state !== 'ready') return null;

  return (
    <div className="space-y-8">
      {MATERIAL_GROUPS.map((group) => {
        const items = materials.filter((material) => material.type === group.type);
        if (items.length === 0) return null;

        return (
          <section key={group.type} aria-labelledby={`materials-${group.type}`} className="space-y-4">
            <div>
              <p className="text-xs uppercase tracking-[0.14em] text-brand-reference-muted/55">{group.eyebrow}</p>
              <h2
                id={`materials-${group.type}`}
                className="mt-2 font-referenceHeading text-[clamp(1.65rem,5vw,2.25rem)] font-normal leading-tight text-brand-reference-text"
              >
                {group.title}
              </h2>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              {items.map((material) => (
                <MaterialCard key={material.id} material={material} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

function MaterialCard({ material }: { material: PublicMaterial }) {
  const sourceLabel = material.type === 'book' ? 'Открыть источник' : material.type === 'article' ? 'Перейти к источнику' : 'Открыть материал';

  return (
    <article className="rounded-[6px] border border-brand-reference-line/30 bg-brand-reference-panel px-5 py-5 shadow-referenceCard sm:px-6 sm:py-6">
      {material.media_url && material.type !== 'audio' ? (
        <div className="mb-5 overflow-hidden rounded-[5px] border border-brand-reference-line/20 bg-brand-reference-panelDeep">
          <img src={material.media_url} alt="" loading="lazy" className="aspect-[16/10] w-full object-cover" />
        </div>
      ) : null}

      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs uppercase tracking-[0.12em] text-brand-reference-muted/55">
          <span>{materialTypeLabel(material.type)}</span>
          {material.published_at ? <time dateTime={material.published_at}>{DATE.format(new Date(material.published_at))}</time> : null}
        </div>

        <h3 className="font-referenceHeading text-[clamp(1.45rem,4vw,1.9rem)] font-normal leading-tight text-brand-reference-text">
          {material.title}
        </h3>

        {material.author ? <p className="text-sm font-light text-brand-reference-muted/80">{material.author}</p> : null}

        <div className="h-px bg-brand-reference-line/65" />
        <p className="text-[15px] font-light leading-7 text-brand-reference-muted">{material.excerpt}</p>

        {material.body ? (
          <details className="pt-1 text-[15px] font-light leading-7 text-brand-reference-muted">
            <summary className="cursor-pointer select-none font-semibold text-brand-reference-text">Читать полностью</summary>
            <div className="mt-3 whitespace-pre-wrap">{material.body}</div>
          </details>
        ) : null}

        <div className="flex flex-wrap gap-4 pt-2">
          {material.type === 'video' ? (
            <Link
              to="/video"
              className="inline-flex border-b border-brand-reference-red pb-1 text-sm font-semibold uppercase tracking-[0.08em] text-brand-reference-text transition-colors hover:text-white"
            >
              Смотреть видео
            </Link>
          ) : null}
          {material.source_url ? (
            <a
              href={material.source_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex border-b border-brand-reference-line pb-1 text-sm font-semibold uppercase tracking-[0.08em] text-brand-reference-text transition-colors hover:text-white"
            >
              {sourceLabel}
            </a>
          ) : null}
        </div>
      </div>
    </article>
  );
}

function materialTypeLabel(type: PublicMaterialType): string {
  switch (type) {
    case 'book':
      return 'Книга';
    case 'video':
      return 'Видео';
    case 'audio':
      return 'Аудио';
    case 'article':
      return 'Статья';
    default:
      return 'Материал';
  }
}

function MaterialLink({
  to,
  eyebrow,
  title,
  text,
}: {
  to: string;
  eyebrow: string;
  title: string;
  text: string;
}) {
  return (
    <Link to={to} className="block focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-reference-line">
      <ReferencePanel className="h-full transition-colors hover:border-brand-reference-line/55">
        <p className="text-xs uppercase tracking-[0.14em] text-brand-reference-muted/55">{eyebrow}</p>
        <h2 className="mt-2 font-referenceHeading text-[clamp(1.55rem,5vw,2rem)] font-normal leading-tight text-brand-reference-text">
          {title}
        </h2>
        <div className="my-5 h-px bg-brand-reference-line/70" />
        <p className="text-[15px] font-light leading-7 text-brand-reference-muted">{text}</p>
      </ReferencePanel>
    </Link>
  );
}
