import { EditorialNote } from '../components/EditorialNote';
import { Heraldry } from '../components/Heraldry';
import { InternalHero } from '../components/InternalHero';
import { MonumentHeading } from '../components/MonumentHeading';
import { Section } from '../components/Section';

export function AboutPage() {
  return (
    <>
      <InternalHero eyebrow="Astrea" title="О ложе" lead="Раздел для утвержденной информации о Достопочтенной Ложе «Астрея» № 3." />
      <Section>
        <div className="mx-auto max-w-3xl">
          <MonumentHeading title="Официальное вступление готовится" />
          <div className="mt-10">
            <EditorialNote>Содержательные сведения, даты и организационный текст будут опубликованы после утверждения.</EditorialNote>
          </div>
        </div>
      </Section>
      <Section tone="alternate">
        <div className="mx-auto max-w-3xl">
          <MonumentHeading title="Исторические материалы" lead="Архивные и справочные материалы находятся в редакционной подготовке." />
        </div>
      </Section>
      <Section>
        <div className="mx-auto max-w-3xl">
          <MonumentHeading title="Астрея и Санкт-Петербург" lead="Нейтральный раздел для утвержденного текста о петербургском контексте." />
        </div>
      </Section>
      <Section tone="dark">
        <div className="mx-auto max-w-3xl">
          <MonumentHeading title="Официальная символика" lead="На сайте используются только предоставленные клиентом официальные изображения." />
          <div className="mt-10">
            <Heraldry />
          </div>
        </div>
      </Section>
    </>
  );
}
