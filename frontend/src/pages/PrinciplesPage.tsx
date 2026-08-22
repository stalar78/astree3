import { EditorialNote } from '../components/EditorialNote';
import { InternalHero } from '../components/InternalHero';
import { ReservedRow } from '../components/ReservedRow';
import { Section } from '../components/Section';

export function PrinciplesPage() {
  return (
    <>
      <InternalHero eyebrow="Материалы" title="Цели и принципы" lead="Раздел для утвержденного редакционного текста." />
      <Section>
        <div className="mx-auto max-w-4xl">
          <EditorialNote>Доктринальные формулировки не создаются самостоятельно. Официальный текст готовится.</EditorialNote>
          <div className="mt-14">
            {['Раздел I', 'Раздел II', 'Раздел III', 'Раздел IV'].map((label) => (
              <ReservedRow key={label} label={label} title="официальный текст готовится" />
            ))}
          </div>
        </div>
      </Section>
    </>
  );
}
