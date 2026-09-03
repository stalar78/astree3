import { useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';

import { ReferenceInnerPage, ReferencePanel } from '../components/ReferenceInnerPage';
import { usePublicManagedPage } from '../publicContent/usePublicManagedPage';
import { applyDocumentSeo, seoDescriptionFromText, siteTitle } from '../seo/seo';

const FALLBACK_TITLE = 'Материалы';
const FALLBACK_LEAD = 'Публикации, новости и видеоматериалы Д.·. Л.·. «Астрея» №3.';

export function MaterialsPage() {
  const location = useLocation();
  const { status, page } = usePublicManagedPage('materials');
  const readyPage = status === 'ready' && page ? page : null;
  const title = readyPage?.title ?? FALLBACK_TITLE;
  const description = readyPage ? seoDescriptionFromText(readyPage.content, FALLBACK_LEAD) : FALLBACK_LEAD;

  useEffect(() => {
    applyDocumentSeo({
      title: siteTitle(title),
      description,
      pathname: location.pathname,
      indexable: true,
    });
  }, [description, location.pathname, title]);

  return (
    <ReferenceInnerPage eyebrow="Материалы" title={title} lead={readyPage ? undefined : FALLBACK_LEAD}>
      <div className="space-y-6">
        {readyPage ? (
          <ReferencePanel>
            <div className="whitespace-pre-wrap text-[15px] font-light leading-8 text-brand-reference-muted">{readyPage.content}</div>
          </ReferencePanel>
        ) : null}

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
