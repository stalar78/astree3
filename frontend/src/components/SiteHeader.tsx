import { useState } from 'react';
import { NavLink } from 'react-router-dom';

const navigation = [
  ['История', '/o-lozhe'],
  ['События', '/novosti'],
  ['Медиа', '/video'],
  ['Материалы', null],
  ['Кандидату', '/vstuplenie'],
  ['Контакты', '/kontakty'],
] as const;

export function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="relative z-20 bg-brand-reference-shell text-brand-reference-text shadow-headerGlow">
      <a
        href="#content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:bg-white focus:px-4 focus:py-2 focus:text-black"
      >
        К содержанию
      </a>

      <div className="relative mx-auto max-w-[1534px] px-5 pb-4 pt-5 lg:px-8 lg:pb-0 lg:pt-7">
        <div className="grid min-h-[108px] grid-cols-[86px_1fr] items-center gap-4 pr-0 lg:grid-cols-[138px_minmax(0,1fr)_250px] lg:gap-8 lg:pr-0">
          <NavLink to="/" aria-label="На главную" className="justify-self-start">
            <img
              className="h-[84px] w-[84px] object-contain drop-shadow-[0_0_14px_rgba(94,127,190,0.25)] lg:h-[146px] lg:w-[146px]"
              src="/brand/symbols/symbol-06.png"
              alt=""
            />
          </NavLink>

          <div className="min-w-0 text-left lg:text-center">
            <p className="font-referenceHeading text-[clamp(1.55rem,2.45vw,2.65rem)] font-normal leading-tight tracking-normal text-brand-reference-text">
              Д.·. Л.·. «Астрея» №3 на Востоке г. Санкт-Петербурга
            </p>
          </div>

          <div className="hidden self-start justify-self-end lg:block" aria-hidden="true">
            <img
              className="relative z-30 -mb-[94px] h-[270px] w-[212px] object-contain object-top drop-shadow-[0_0_20px_rgba(95,124,185,0.38)]"
              src="/brand/astrea-standard-transparent.png"
              alt=""
            />
          </div>
        </div>
      </div>

      <div aria-hidden="true">
        <div className="h-[8px] bg-brand-reference-white" />
        <div className="h-[7px] bg-brand-reference-red" />
      </div>

      <div className="mx-auto max-w-[1534px] px-5 lg:px-8">
        <div className="flex min-h-[78px] items-center lg:pr-[250px]">
          <nav className="hidden w-full items-center justify-center gap-10 text-[20px] font-light text-brand-reference-muted lg:flex" aria-label="Основная навигация">
            {navigation.map(([label, href]) =>
              href ? (
                <NavLink
                  key={label}
                  to={href}
                  className={({ isActive }) =>
                    `transition-colors hover:text-white focus:text-white ${isActive ? 'text-white' : ''}`
                  }
                >
                  {label}
                </NavLink>
              ) : (
                <span key={label} aria-disabled="true" className="cursor-default text-brand-reference-muted/70" title="Раздел будет подключен после уточнения назначения">
                  {label}
                </span>
              ),
            )}
          </nav>

          <button
            className="ml-auto border border-white/20 px-4 py-2 text-sm uppercase tracking-[0.12em] text-brand-reference-text lg:hidden"
            type="button"
            aria-expanded={open}
            aria-controls="mobile-nav"
            onClick={() => setOpen((value) => !value)}
          >
            Меню
          </button>
        </div>
      </div>

      {open ? (
        <nav id="mobile-nav" className="border-t border-white/10 bg-brand-reference-panelDeep px-5 py-4 lg:hidden" aria-label="Мобильная навигация">
          <div className="mx-auto grid max-w-[1534px] gap-1 text-base text-brand-reference-muted">
            {navigation.map(([label, href]) =>
              href ? (
                <NavLink key={label} to={href} onClick={() => setOpen(false)} className="py-2 hover:text-white">
                  {label}
                </NavLink>
              ) : (
                <span key={label} aria-disabled="true" className="py-2 text-brand-reference-muted/55">
                  {label}
                </span>
              ),
            )}
          </div>
        </nav>
      ) : null}
    </header>
  );
}
