import { EditorialNote } from '../components/EditorialNote';
import { InternalHero } from '../components/InternalHero';
import { Section } from '../components/Section';

export function NewsPage() {
  return (
    <>
      <InternalHero eyebrow="Архив" title="Новости" lead="Новостной раздел подготовлен для утвержденных публикаций." />
      <Section>
        <div className="mx-auto max-w-4xl">
          <EditorialNote title="Новостей пока нет">Утвержденные новости еще не опубликованы. Раздел сохранен как официальный архивный экран без демонстрационных материалов.</EditorialNote>
        </div>
      </Section>
    </>
  );
}
