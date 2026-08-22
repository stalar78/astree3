import { Action } from '../components/Action';
import { EditorialNote } from '../components/EditorialNote';
import { Heraldry } from '../components/Heraldry';
import { MonumentHeading } from '../components/MonumentHeading';
import { OrnamentDivider } from '../components/OrnamentDivider';
import { Section } from '../components/Section';

export function HomePage() {
  return (
    <>
      <section className="relative overflow-hidden bg-brand-black text-white">
        <div className="absolute inset-y-0 right-0 hidden w-1/2 bg-[radial-gradient(circle_at_center,rgba(218,41,28,0.18),transparent_55%)] lg:block" aria-hidden="true" />
        <div className="mx-auto grid min-h-[calc(100vh-73px)] max-w-7xl items-center gap-10 px-5 py-14 lg:grid-cols-[0.95fr_1.05fr] lg:px-8">
          <div className="relative z-10 max-w-2xl">
            <Heraldry />
            <p className="mt-10 text-xs font-semibold uppercase text-brand-red">На Востоке Санкт-Петербурга</p>
            <h1 className="mt-5 font-display text-5xl leading-none md:text-7xl lg:text-8xl">Д.Л. «Астрея» № 3</h1>
            <p className="mt-7 max-w-xl text-lg leading-8 text-brand-gray6">
              Официальный сайт Достопочтенной Ложи «Астрея» № 3. Публичные материалы публикуются после утверждения.
            </p>
            <div className="mt-10 flex flex-col gap-4 sm:flex-row">
              <Action to="/vstuplenie">Вступить</Action>
              <Action to="/o-lozhe" variant="secondary">О ложе</Action>
            </div>
          </div>
          <div className="relative min-h-[420px] lg:min-h-[650px]">
            <div className="absolute inset-8 rounded-full bg-white/10 blur-3xl" aria-hidden="true" />
            <img
              className="relative z-10 mx-auto h-full max-h-[720px] w-full object-contain drop-shadow-[0_32px_80px_rgba(0,0,0,0.45)]"
              src="/brand/astrea-standard-transparent.png"
              alt="Штандарт Достопочтенной Ложи «Астрея» № 3"
            />
          </div>
        </div>
      </section>
      <Section>
        <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr]">
          <MonumentHeading title="Официальное пространство для утвержденных материалов" lead="Структура сайта подготовлена для публичных разделов, новостей, видео и кандидатского обращения без выдуманного содержания." />
          <div className="space-y-8">
            <EditorialNote>Исторические, организационные и правовые тексты будут опубликованы после утверждения клиентом.</EditorialNote>
            <OrnamentDivider />
          </div>
        </div>
      </Section>
      <Section tone="dark">
        <div className="grid gap-10 md:grid-cols-3">
          {['Новости', 'Видео', 'Вступление'].map((item) => (
            <div key={item} className="border-t border-white/20 pt-6">
              <p className="font-display text-3xl">{item}</p>
              <p className="mt-4 text-sm leading-6 text-brand-gray6">Раздел подготовлен в утвержденной институциональной композиции и ожидает проверенных материалов.</p>
            </div>
          ))}
        </div>
      </Section>
    </>
  );
}
