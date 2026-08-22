import { EditorialNote } from '../components/EditorialNote';
import { InternalHero } from '../components/InternalHero';
import { ReservedRow } from '../components/ReservedRow';
import { Section } from '../components/Section';

export function FaqPage() {
  return (
    <>
      <InternalHero eyebrow="Вопросы" title="FAQ" lead="Раздел ответов на вопросы ожидает утвержденного содержания." />
      <Section>
        <div className="mx-auto max-w-4xl">
          <EditorialNote>Ответы не заполнены, чтобы не публиковать неподтвержденную информацию.</EditorialNote>
          <div className="mt-14">
            {['Вопрос 01', 'Вопрос 02', 'Вопрос 03'].map((label) => (
              <ReservedRow key={label} label={label} />
            ))}
          </div>
        </div>
      </Section>
    </>
  );
}
