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
        <div className="mx-auto max-w-3xl">
          <MonumentHeading eyebrow="Официальное обращение" title="О ложе" />
          <div className="mt-10 space-y-6 font-serifBody text-lg leading-8 text-brand-ink/80">
            <p>Настоящий сайт является официальным представительством Достопочтенной Ложи «Астрея» № 3, работающей на Востоке города Санкт-Петербурга.</p>
            <p>На сайте размещаются сведения о ложе, исторические и информационные материалы, официальные сообщения, видеозаписи и информация для тех, кто желает обратиться с заявлением о вступлении.</p>
          </div>
          <div className="mt-12">
            <OrnamentDivider />
          </div>
        </div>
      </Section>
      <Section tone="dark">
        <div className="mx-auto max-w-4xl">
          <MonumentHeading
            eyebrow="История и преемственность"
            title="Хронология"
            lead="Раздел находится в редакционной подготовке. Документальные подтверждения и архивные материалы будут опубликованы по мере проверки источников."
          />
          <div className="mt-14">
            <ChronologyRow
              marker="MDCCLXXV"
              meta="Дата на символике"
              text="Дата, присутствующая на официальной символике ложи. Историческое пояснение будет добавлено после редакционной проверки материалов."
            />
            <ChronologyRow marker="Архив" meta="Материалы готовятся" text="Исторические тексты и документы будут перенесены после отбора и проверки заказчиком." />
          </div>
        </div>
      </Section>
      <Section tone="alternate">
        <div className="mx-auto max-w-4xl">
          <MonumentHeading
            eyebrow="Положение ложи"
            title="Место в масонской структуре"
            lead="На сайте используется официальная символика Великой Ложи России и Провинции Северо-Запад. Достопочтенная Ложа «Астрея» № 3 работает на Востоке Санкт-Петербурга."
          />
          <div className="mt-14 grid gap-10 md:grid-cols-2">
            <SymbolBlock src="/brand/grand-lodge-russia-emblem.png" alt="Эмблема Великой Ложи России" caption="Великая Ложа России" />
            <SymbolBlock src="/brand/province-northwest-emblem.png" alt="Эмблема Провинции Северо-Запад" caption="Провинция Северо-Запад" />
          </div>
        </div>
      </Section>
      <Section>
        <div className="mx-auto max-w-3xl">
          <MonumentHeading eyebrow="Официальные сообщения" title="Новости ложи" />
          <div className="mt-10">
            <EditorialNote>Официальные сообщения будут опубликованы после предоставления и редакционной проверки материалов.</EditorialNote>
          </div>
          <div className="mt-8">
            <Action to="/novosti" variant="secondary">Все сообщения</Action>
          </div>
        </div>
      </Section>
      <Section tone="dark">
        <div className="mx-auto max-w-3xl">
          <MonumentHeading eyebrow="Собрание материалов" title="Видеоархив" lead="Раздел для публикации согласованных видеоматериалов." />
          <div className="mt-10 border-y border-white/15 py-8">
            <p className="font-serifBody text-lg leading-8 text-brand-gray6">Видеоматериалы будут добавлены после согласования ссылок. Основной источник размещения — RuTube.</p>
          </div>
        </div>
      </Section>
      <Section>
        <div className="mx-auto max-w-4xl">
          <MonumentHeading eyebrow="Кандидатам" title="О подаче прошения" />
          <div className="mt-14">
            {[
              ['I', 'Ознакомиться с информацией о вступлении и требованиями, которые будут перенесены с действующего сайта и утверждены заказчиком.'],
              ['II', 'Подтвердить понимание, что заявление подаётся в ложу, работающую в Санкт-Петербурге.'],
              ['III', 'Заполнить анкету и при необходимости приложить фотографию и ссылки на публичные профили.'],
              ['IV', 'Подтвердить необходимые согласия на обработку персональных данных и политику конфиденциальности.'],
            ].map(([marker, text]) => (
              <div key={marker} className="grid gap-4 border-t border-brand-gray10/30 py-7 md:grid-cols-[90px_1fr]">
                <p className="font-display text-3xl text-brand-red">{marker}</p>
                <p className="font-serifBody text-lg leading-8 text-brand-ink/80">{text}</p>
              </div>
            ))}
          </div>
          <div className="mt-10">
            <Action to="/vstuplenie">Раздел для кандидатов</Action>
            <p className="mt-4 font-serifBody text-sm text-brand-ink/65">Форма прошения будет открыта позднее</p>
          </div>
        </div>
      </Section>
    </>
  );
}

function ChronologyRow({ marker, meta, text }: { marker: string; meta: string; text: string }) {
  return (
    <div className="grid gap-5 border-t border-white/15 py-8 md:grid-cols-[160px_180px_1fr]">
      <p className="font-display text-3xl text-white">{marker}</p>
      <p className="text-sm uppercase text-brand-gray6">{meta}</p>
      <p className="font-serifBody text-lg leading-8 text-brand-gray6">{text}</p>
    </div>
  );
}

function SymbolBlock({ src, alt, caption }: { src: string; alt: string; caption: string }) {
  return (
    <figure className="border-t border-brand-gray10/30 pt-8 text-center">
      <img className="mx-auto h-32 w-32 object-contain md:h-40 md:w-40" src={src} alt={alt} />
      <figcaption className="mt-6">
        <p className="font-display text-3xl text-brand-ink">{caption}</p>
        <p className="mt-3 font-serifBody text-base leading-7 text-brand-ink/70">Официальная символика, используемая на сайте.</p>
      </figcaption>
    </figure>
  );
}
