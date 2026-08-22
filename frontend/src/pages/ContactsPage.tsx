import { EditorialNote } from '../components/EditorialNote';
import { InternalHero } from '../components/InternalHero';
import { Section } from '../components/Section';

export function ContactsPage() {
  return (
    <>
      <InternalHero eyebrow="Связь" title="Контакты" lead="Раздел для утвержденной контактной информации." />
      <Section>
        <div className="mx-auto max-w-4xl">
          <EditorialNote>Контактные данные, адреса и способы связи не публикуются до утверждения клиентом.</EditorialNote>
        </div>
      </Section>
    </>
  );
}
