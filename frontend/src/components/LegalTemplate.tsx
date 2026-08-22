import { EditorialNote } from './EditorialNote';
import { InternalHero } from './InternalHero';
import { ReservedRow } from './ReservedRow';
import { Section } from './Section';

type LegalTemplateProps = {
  title: string;
  lead: string;
  sections: string[];
};

export function LegalTemplate({ title, lead, sections }: LegalTemplateProps) {
  return (
    <>
      <InternalHero eyebrow="Правовой документ" title={title} lead={lead} />
      <Section>
        <div className="mx-auto max-w-3xl">
          <EditorialNote title="Документ не утвержден">Юридический текст не опубликован до правовой проверки и утверждения.</EditorialNote>
          <div className="mt-14">
            {sections.map((section, index) => (
              <ReservedRow key={section} label={`${index + 1}.`} title={section} />
            ))}
          </div>
        </div>
      </Section>
    </>
  );
}
