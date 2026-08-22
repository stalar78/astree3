import { EditorialNote } from '../components/EditorialNote';
import { InternalHero } from '../components/InternalHero';
import { Section } from '../components/Section';

export function VideoPage() {
  return (
    <>
      <InternalHero eyebrow="Видеоматериалы" title="Видео" lead="Раздел предназначен для утвержденных внешних ссылок, преимущественно RuTube." />
      <Section>
        <div className="mx-auto max-w-4xl">
          <EditorialNote title="Видео пока не опубликованы">Внешние ссылки и описания видео будут добавлены после утверждения. Собственный видеохостинг и потоковая передача не реализуются.</EditorialNote>
        </div>
      </Section>
    </>
  );
}
