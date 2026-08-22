import { EditorialNote } from '../components/EditorialNote';
import { InternalHero } from '../components/InternalHero';
import { MonumentHeading } from '../components/MonumentHeading';
import { Section } from '../components/Section';

type EditorialKind = 'about' | 'lodges' | 'principles' | 'faq' | 'privacy' | 'consent';

const pageMap: Record<EditorialKind, { title: string; eyebrow: string; lead: string; note: string }> = {
  about: {
    title: 'О ложе',
    eyebrow: 'Astrea',
    lead: 'Раздел для утвержденной информации о Достопочтенной Ложе «Астрея» № 3.',
    note: 'Содержательная история, даты и организационные сведения не добавлены до редакционного утверждения.',
  },
  lodges: {
    title: 'Ложи Санкт-Петербурга',
    eyebrow: 'Санкт-Петербург',
    lead: 'Редакционный раздел о петербургском контексте.',
    note: 'Иерархия, перечни и справочные материалы не публикуются без утвержденного источника.',
  },
  principles: {
    title: 'Цели и принципы',
    eyebrow: 'Материалы',
    lead: 'Раздел для утвержденного текста о целях и принципах.',
    note: 'Доктринальные формулировки и требования к кандидатам не сформулированы самостоятельно.',
  },
  faq: {
    title: 'FAQ',
    eyebrow: 'Вопросы',
    lead: 'Раздел ответов на вопросы, ожидающий утвержденного содержания.',
    note: 'Ответы не заполнены, чтобы не вводить посетителей в заблуждение неподтвержденной информацией.',
  },
  privacy: {
    title: 'Политика конфиденциальности',
    eyebrow: 'Правовая информация',
    lead: 'Страница для утвержденной политики конфиденциальности.',
    note: 'Юридический текст будет размещен после проверки и утверждения.',
  },
  consent: {
    title: 'Согласие на обработку данных',
    eyebrow: 'Правовая информация',
    lead: 'Страница для утвержденного текста согласия.',
    note: 'Текст согласия и версии документов не заполняются до правового утверждения.',
  },
};

export function EditorialPage({ kind }: { kind: EditorialKind }) {
  const page = pageMap[kind];

  return (
    <>
      <InternalHero eyebrow={page.eyebrow} title={page.title} lead={page.lead} />
      <Section>
        <div className="mx-auto max-w-4xl">
          <MonumentHeading title="Материал ожидает публикации" />
          <div className="mt-10">
            <EditorialNote>{page.note}</EditorialNote>
          </div>
        </div>
      </Section>
    </>
  );
}
