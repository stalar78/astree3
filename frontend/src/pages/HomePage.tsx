import { Action } from '../components/Action';
import { EditorialNote } from '../components/EditorialNote';
import { MonumentHeading } from '../components/MonumentHeading';
import { OrnamentDivider } from '../components/OrnamentDivider';
import { Section } from '../components/Section';

export function HomePage() {
  return (
    <>
      <section className="relative overflow-hidden bg-brand-black text-white">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(218,41,28,0.16),transparent_48%)]" aria-hidden="true" />
        <div className="relative mx-auto flex min-h-[calc(100vh-210px)] max-w-5xl flex-col items-center justify-center px-5 py-16 text-center lg:px-8 lg:py-24">
          <p className="text-xs font-semibold uppercase text-brand-gray6 md:text-sm">Великая Ложа России · Провинция Северо-Запад</p>
          <div className="relative mt-10 w-full">
            <div className="absolute inset-0 mx-auto h-72 w-72 rounded-full bg-white/10 blur-3xl" aria-hidden="true" />
            <img
              className="relative z-10 mx-auto w-[78vw] max-w-[420px] object-contain drop-shadow-[0_32px_80px_rgba(0,0,0,0.5)]"
              src="/brand/astrea-standard-transparent.png"
              alt="Штандарт Достопочтенной Ложи «Астрея» № 3"
            />
          </div>
          <h1 className="mt-10 max-w-4xl font-display text-5xl leading-none md:text-7xl">Достопочтенная Ложа «Астрея» № 3</h1>
          <p className="mt-5 font-serifBody text-xl text-brand-gray6">на Востоке Санкт-Петербурга</p>
          <div className="mt-10 w-full">
            <OrnamentDivider tone="dark" />
          </div>
          <p className="mt-8 max-w-2xl font-serifBody text-lg leading-8 text-brand-gray6">Официальный сайт. Публичные материалы публикуются после утверждения.</p>
          <p className="mt-8 font-display text-2xl text-brand-gray6">MDCCLXXV</p>
          <div className="mt-10 flex flex-col justify-center gap-4 sm:flex-row">
            <Action to="/o-lozhe" variant="secondary">О ложе</Action>
            <Action to="/vstuplenie">Подать прошение</Action>
          </div>
        </div>
      </section>
      <Section>
        <div className="mx-auto max-w-4xl text-center">
          <div className="text-left">
            <MonumentHeading title="Официальное пространство для утвержденных материалов" lead="Структура сайта подготовлена для публичных разделов, новостей, видео и кандидатского обращения без выдуманного содержания." />
          </div>
          <div className="mt-12 space-y-8">
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
