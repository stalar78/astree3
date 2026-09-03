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

function TricolorBand() {
  return (
    <div aria-hidden="true" className="relative z-10">
      <div className="h-[4px] bg-white" />
      <div className="h-[4px] bg-brand-reference-flagBlue" />
      <div className="h-[4px] bg-brand-reference-flagRed" />
    </div>
  );
}

export function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="relative z-20 bg-brand-reference-shell text-brand-reference-text">
      <a
        href="#content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:bg-white focus:px-4 focus:py-2 focus:text-black"
      >
        К содержанию
      </a>

      <div className="relative mx-auto hidden h-[118px] max-w-[1534px] lg:block">
        <NavLink to="/" aria-label="На главную" className="absolute left-8 top-[38px] z-30 block xl:left-10">
          <img
            className="h-[138px] w-[138px] object-contain drop-shadow-[0_0_12px_rgba(21,59,147,0.28)]"
            src="/brand/symbols/symbol-06.png"
            alt=""
          />
        </NavLink>

        <div className="flex h-full items-center justify-center px-[240px] pb-2 text-center">
          <p className="font-referenceHeading text-[clamp(1.9rem,2.25vw,2.2rem)] font-normal leading-none tracking-normal text-brand-reference-text">
            Д.·. Л.·. «Астрея» №3 на Востоке г. Санкт-Петербурга
          </p>
        </div>

        <div className="absolute right-6 top-[18px] z-30 xl:right-8" aria-hidden="true">
          <img
            className="h-[282px] w-[220px] object-contain object-top drop-shadow-[0_0_9px_rgba(166,177,255,0.5)] drop-shadow-[0_0_24px_rgba(75,93,190,0.34)] drop-shadow-[0_14px_22px_rgba(0,0,0,0.58)]"
            src="/brand/astrea-standard-transparent.png"
            alt=""
          />
        </div>
      </div>

      <div className="grid min-h-[104px] grid-cols-[84px_1fr] items-center gap-4 px-5 py-4 lg:hidden">
        <NavLink to="/" aria-label="На главную">
          <img className="h-20 w-20 object-contain" src="/brand/symbols/symbol-06.png" alt="" />
        </NavLink>
        <p className="font-referenceHeading text-[clamp(1.35rem,5vw,1.85rem)] leading-tight text-brand-reference-text">
          Д.·. Л.·. «Астрея» №3 на Востоке г. Санкт-Петербурга
        </p>
      </div>

      <TricolorBand />

      <div className="relative mx-auto max-w-[1534px] px-5 lg:px-8">
        <div className="flex min-h-[68px] items-center lg:px-[155px] lg:pr-[245px]">
          <nav className="hidden w-full items-center justify-center gap-10 text-[17px] font-light text-brand-reference-muted lg:flex" aria-label="Основная навигация">
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
