import { Link, useParams } from 'react-router-dom';
import { EditorialNote } from '../components/EditorialNote';
import { InternalHero } from '../components/InternalHero';
import { Section } from '../components/Section';

export function NewsArticlePage() {
  const { slug } = useParams();

  return (
    <>
      <InternalHero eyebrow="Новости" title="Материал не опубликован" lead="Запрошенный материал отсутствует в утвержденном архиве." />
      <Section>
        <div className="mx-auto max-w-4xl">
          <EditorialNote>
            {`Материал${slug ? ` «${slug}»` : ''} не опубликован. На странице не используется демонстрационный или вымышленный текст.`}
          </EditorialNote>
          <Link className="mt-8 inline-block border-b border-brand-red pb-1 text-sm font-semibold uppercase text-brand-black" to="/novosti">
            Вернуться к новостям
          </Link>
        </div>
      </Section>
    </>
  );
}
