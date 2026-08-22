import { EditorialNote } from '../components/EditorialNote';
import { InternalHero } from '../components/InternalHero';
import { ReservedRow } from '../components/ReservedRow';
import { Section } from '../components/Section';

export function LodgesPage() {
  return (
    <>
      <InternalHero eyebrow="Справочный раздел" title="Ложи Санкт-Петербурга" lead="Серьезный архивный раздел для будущего утвержденного каталога." />
      <Section>
        <div className="mx-auto max-w-4xl">
          <EditorialNote>Перечни, хронология и справочные сведения не публикуются без утвержденных источников.</EditorialNote>
          <div className="mt-14">
            <ReservedRow label="Каталог" title="будущий утвержденный перечень" />
            <ReservedRow label="Хронология" title="будущая утвержденная хронология" />
            <ReservedRow label="Архив" title="будущие справочные материалы" />
          </div>
        </div>
      </Section>
    </>
  );
}
