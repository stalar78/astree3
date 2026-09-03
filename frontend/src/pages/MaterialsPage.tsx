import { Link } from 'react-router-dom';

import { ReferenceInnerPage, ReferencePanel } from '../components/ReferenceInnerPage';

export function MaterialsPage() {
  return (
    <ReferenceInnerPage
      eyebrow="Материалы"
      title="Материалы"
      lead="Публикации, новости и видеоматериалы Д.·. Л.·. «Астрея» №3."
    >
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
