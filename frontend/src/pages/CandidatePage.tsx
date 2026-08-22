import { InternalHero } from '../components/InternalHero';
import { OrnamentDivider } from '../components/OrnamentDivider';
import { Section } from '../components/Section';

const fields = [
  ['Фамилия, имя, отчество', 'text'],
  ['Дата рождения', 'text'],
  ['Город проживания', 'text'],
  ['Телефон', 'tel'],
  ['Email', 'email'],
  ['Образование', 'text'],
  ['Работа / род занятий', 'text'],
  ['Семейное положение', 'text'],
  ['Членство в иных организациях', 'text'],
  ['VK / публичные социальные ссылки', 'url'],
];

export function CandidatePage() {
  return (
    <>
      <InternalHero eyebrow="Кандидату" title="Вступление" lead="Статичная визуальная форма обращения. Отправка, загрузка и сохранение данных на этом этапе не выполняются." />
      <Section>
        <form className="mx-auto max-w-4xl space-y-14" onSubmit={(event) => event.preventDefault()} noValidate>
          <fieldset className="border-y border-brand-gray10/30 py-10">
            <legend className="px-0 font-display text-4xl">Анкета кандидата</legend>
            <div className="mt-8 grid gap-6 md:grid-cols-2">
              {fields.map(([label, type]) => (
                <label key={label} className="grid gap-2 text-sm font-semibold uppercase text-brand-ink">
                  {label}
                  <input className="border border-brand-gray10/40 bg-white px-4 py-3 text-base font-normal normal-case text-brand-ink outline-none focus:border-brand-red" type={type} disabled />
                </label>
              ))}
            </div>
          </fieldset>
          <fieldset className="border-y border-brand-gray10/30 py-10">
            <legend className="px-0 font-display text-4xl">Обращение</legend>
            <label className="mt-8 grid gap-2 text-sm font-semibold uppercase text-brand-ink">
              О себе / мотивация
              <textarea className="min-h-40 border border-brand-gray10/40 bg-white px-4 py-3 text-base font-normal normal-case text-brand-ink outline-none focus:border-brand-red" disabled />
            </label>
          </fieldset>
          <fieldset className="border-y border-brand-gray10/30 py-10">
            <legend className="px-0 font-display text-4xl">Фотография</legend>
            <div className="mt-6 border border-dashed border-brand-gray10/50 bg-white/60 px-6 py-10 text-center">
              <p className="text-base font-semibold">JPG, PNG или WebP</p>
              <p className="mt-2 text-sm leading-6 text-brand-ink/70">Загрузка файла не выполняется на Stage 3. В будущей версии фотография будет храниться приватно и не будет доступна публично.</p>
            </div>
          </fieldset>
          <fieldset className="border-y border-brand-gray10/30 py-10">
            <legend className="px-0 font-display text-4xl">Подтверждения</legend>
            <div className="mt-6 space-y-4">
              {[
                'Подтверждаю, что обращение направляется в ложу, работающую в Санкт-Петербурге.',
                'Подтверждаю ознакомление с будущей политикой конфиденциальности.',
                'Подтверждаю согласие с будущими условиями обработки персональных данных.',
              ].map((label) => (
                <label key={label} className="flex gap-3 text-sm leading-6 text-brand-ink/80">
                  <input className="mt-1 h-4 w-4 accent-brand-red" type="checkbox" disabled />
                  <span>{label}</span>
                </label>
              ))}
            </div>
          </fieldset>
          <OrnamentDivider />
          <div className="text-center">
            <button className="border border-brand-red bg-brand-red px-6 py-3 text-sm font-semibold uppercase text-white opacity-60" type="submit" disabled>
              Отправка недоступна
            </button>
            <p className="mt-4 text-sm leading-6 text-brand-ink/70">Форма является визуальным прототипом. API, сохранение и email-уведомления будут реализованы на backend stage.</p>
          </div>
        </form>
      </Section>
    </>
  );
}
