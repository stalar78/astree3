import { NavLink } from 'react-router-dom';
import { useState } from 'react';
import { Action } from './Action';

const navigation = [
  ['О ложе', '/o-lozhe'],
  ['Ложи Санкт-Петербурга', '/lozhi-sankt-peterburga'],
  ['Цели и принципы', '/celi-i-principy'],
  ['FAQ', '/faq'],
  ['Новости', '/novosti'],
  ['Видео', '/video'],
  ['Контакты', '/kontakty'],
];

export function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-brand-black/95 text-white backdrop-blur">
      <a href="#content" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:bg-white focus:px-4 focus:py-2 focus:text-brand-black">
        К содержанию
      </a>
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-5 px-5 py-4 lg:px-8">
        <NavLink to="/" className="flex min-w-0 items-center gap-4" aria-label="Astrea home">
          <span className="flex items-center gap-2">
            <img className="h-10 w-10 object-contain" src="/brand/grand-lodge-russia-emblem.png" alt="Эмблема Великой Ложи России" />
            <img className="h-10 w-10 object-contain" src="/brand/province-northwest-emblem.png" alt="Эмблема Северо-Западной Провинции" />
          </span>
          <span className="min-w-0">
            <span className="block font-display text-xl uppercase leading-none tracking-normal">Astrea</span>
            <span className="block truncate text-xs uppercase text-brand-gray6">Д.Л. «Астрея» № 3</span>
          </span>
        </NavLink>
        <nav className="hidden items-center gap-5 text-sm text-brand-gray6 xl:flex" aria-label="Основная навигация">
          {navigation.map(([label, href]) => (
            <NavLink key={href} to={href} className={({ isActive }) => `transition hover:text-white focus:text-white ${isActive ? 'text-white' : ''}`}>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="hidden xl:block">
          <Action to="/vstuplenie">Вступить</Action>
        </div>
        <button
          className="border border-white/25 px-3 py-2 text-sm uppercase text-white xl:hidden"
          type="button"
          aria-expanded={open}
          aria-controls="mobile-nav"
          onClick={() => setOpen((value) => !value)}
        >
          Меню
        </button>
      </div>
      {open ? (
        <nav id="mobile-nav" className="border-t border-white/10 px-5 py-4 xl:hidden" aria-label="Мобильная навигация">
          <div className="mx-auto grid max-w-7xl gap-3 text-sm text-brand-gray6">
            {navigation.map(([label, href]) => (
              <NavLink key={href} to={href} onClick={() => setOpen(false)} className="py-1 hover:text-white">
                {label}
              </NavLink>
            ))}
            <Action to="/vstuplenie" onClick={() => setOpen(false)}>
              Вступить
            </Action>
          </div>
        </nav>
      ) : null}
    </header>
  );
}
