import { EditorialNote } from './EditorialNote';
import { InternalHero } from './InternalHero';
import { Section } from './Section';
import { legalDraftNotice, type LegalDocument, type LegalSection } from '../legal/legalDocuments';

type LegalTemplateProps = {
  document: LegalDocument;
};

export function LegalTemplate({ document }: LegalTemplateProps) {
  return (
    <>
      <InternalHero eyebrow={document.eyebrow} title={document.title} lead={document.lead} />
      <Section>
        <article className="mx-auto max-w-4xl">
          <EditorialNote title="Рабочая редакция">
            {legalDraftNotice}
          </EditorialNote>

          <div className="mt-6 inline-flex rounded-full border border-brand-red/20 bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-brand-red">
            Версия: {document.version}
          </div>

          <div className="mt-12 space-y-12">
            {document.sections.map((section, index) => (
              <LegalSectionBlock key={section.title} index={index} section={section} />
            ))}
          </div>
        </article>
      </Section>
    </>
  );
}

type LegalSectionBlockProps = {
  index: number;
  section: LegalSection;
};

function LegalSectionBlock({ index, section }: LegalSectionBlockProps) {
  const sectionId = `legal-section-${index + 1}`;

  return (
    <section aria-labelledby={sectionId} className="scroll-mt-24 space-y-5">
      <div className="border-t border-brand-gray10/20 pt-8">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-red">{index + 1}</p>
        <h2 id={sectionId} className="mt-3 font-display text-3xl leading-tight text-brand-ink">
          {section.title}
        </h2>
      </div>

      {section.paragraphs?.length ? (
        <div className="space-y-4 text-base leading-8 text-brand-ink/80">
          {section.paragraphs.map((paragraph, paragraphIndex) => (
            <p key={`${sectionId}-p-${paragraphIndex}`}>{paragraph}</p>
          ))}
        </div>
      ) : null}

      {section.items?.length ? (
        <ul className="space-y-3 pl-5 text-base leading-8 text-brand-ink/80 marker:text-brand-red">
          {section.items.map((item, itemIndex) => (
            <li key={`${sectionId}-i-${itemIndex}`}>{item}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
