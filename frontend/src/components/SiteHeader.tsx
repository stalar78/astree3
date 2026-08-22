import { NavLink } from 'react-router-dom';
import { useState } from 'react';
import { OrnamentDivider } from './OrnamentDivider';

const navigation = [
  ['О ложе', '/o-lozhe'],
  ['Цели и принципы', '/celi-i-principy'],
  ['Новости', '/novosti'],
  ['Видео', '/video'],
  ['Кандидатам', '/vstuplenie'],
  ['Контакты', '/kontakty'],
];

const secondaryNavigation = [
  ['Ложи Санкт-Петербурга', '/lozhi-sankt-peterburga'],
  ['Частые вопросы', '/faq'],
  ['Политика конфиденциальности', '/privacy'],
  ['Согласие на обработку данных', '/consent'],
];

export function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="bg-brand-black text-white">
      <a href="#content" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:bg-white focus:px-4 focus:py-2 focus:text-brand-black">
        К содержанию
      </a>
      <div className="mx-auto max-w-7xl px-5 py-6 lg:px-8 lg:py-8">
        <div className="grid grid-cols-[72px_1fr_72px] items-center gap-4 md:grid-cols-[96px_1fr_96px]">
          <NavLink to="/" aria-label="На главную">
            <img className="h-14 w-14 object-contain md:h-20 md:w-20" src="/brand/grand-lodge-russia-emblem.png" alt="Эмблема Великой Ложи России" />
          </NavLink>
          <div className="text-center">
            <p className="font-display text-2xl leading-tight md:text-4xl">Достопочтенная Ложа «Астрея» № 3</p>
            <p className="mt-2 text-xs uppercase text-brand-gray6 md:text-sm">на Востоке Санкт-Петербурга</p>
          </div>
          <NavLink to="/" aria-label="На главную" className="justify-self-end">
            <img className="h-14 w-14 object-contain md:h-20 md:w-20" src="/brand/province-northwest-emblem.png" alt="Эмблема Провинции Северо-Запад" />
          </NavLink>
        </div>
        <div className="my-6">
          <OrnamentDivider tone="dark" />
        </div>
        <nav className="hidden items-center justify-center gap-8 text-sm uppercase text-brand-gray6 lg:flex" aria-label="Основная навигация">
          {navigation.map(([label, href]) => (
            <NavLink key={href} to={href} className={({ isActive }) => `transition hover:text-white focus:text-white ${isActive ? 'text-white' : ''}`}>
              {label}
            </NavLink>
          ))}
        </nav>
        <button
          className="mx-auto block border border-white/25 px-4 py-2 text-sm uppercase text-white lg:hidden"
          type="button"
          aria-expanded={open}
          aria-controls="mobile-nav"
          onClick={() => setOpen((value) => !value)}
        >
          Меню
        </button>
      </div>
      {open ? (
        <nav id="mobile-nav" className="border-t border-white/10 px-5 py-4 lg:hidden" aria-label="Мобильная навигация">
          <div className="mx-auto grid max-w-7xl gap-3 text-sm text-brand-gray6">
            {[...navigation, ...secondaryNavigation].map(([label, href]) => (
              <NavLink key={href} to={href} onClick={() => setOpen(false)} className="py-1 hover:text-white">
                {label}
              </NavLink>
            ))}
          </div>
        </nav>
      ) : null}
    </header>
  );
}
