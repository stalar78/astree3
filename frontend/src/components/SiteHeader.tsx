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

        <div className="absolute right-6 top-[14px] z-30 xl:right-8" aria-hidden="true">
          <img
            className="h-[258px] w-[202px] object-contain object-top"
            style={{
              filter:
                'drop-shadow(0 0 1px rgba(238,240,255,0.98)) drop-shadow(0 0 4px rgba(184,192,255,0.92)) drop-shadow(0 0 10px rgba(121,136,255,0.72)) drop-shadow(0 0 24px rgba(79,96,205,0.46)) drop-shadow(0 12px 18px rgba(0,0,0,0.55))',
            }}
            src="/brand/astrea-standard-transparent.png"
            alt=""
          />
        </div>
      </div>

      <div className="grid min-h-[92px] grid-cols-[64px_minmax(0,1fr)] items-center gap-3 px-4 py-3 sm:min-h-[104px] sm:grid-cols-[84px_minmax(0,1fr)] sm:gap-4 sm:px-5 sm:py-4 lg:hidden">
        <NavLink to="/" aria-label="На главную" className="self-center">
          <img className="h-16 w-16 object-contain sm:h-20 sm:w-20" src="/brand/symbols/symbol-06.png" alt="" />
        </NavLink>
        <p className="min-w-0 break-words font-referenceHeading text-[clamp(1.05rem,5.1vw,1.55rem)] font-normal leading-[1.08] text-brand-reference-text sm:text-[clamp(1.35rem,4.2vw,1.85rem)]">
          Д.·. Л.·. «Астрея» №3 на Востоке г. Санкт-Петербурга
        </p>
      </div>

      <TricolorBand />

      <div className="relative mx-auto max-w-[1534px] px-4 sm:px-5 lg:px-8">
        <div className="flex min-h-[56px] items-center sm:min-h-[64px] lg:min-h-[68px] lg:px-[155px] lg:pr-[225px]">
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
            className="ml-auto inline-flex min-h-10 items-center justify-center rounded-[5px] border border-white/20 px-4 py-2 text-sm uppercase tracking-[0.12em] text-brand-reference-text transition-colors hover:border-white/35 hover:text-white focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-brand-reference-line lg:hidden"
            type="button"
            aria-expanded={open}
            aria-controls="mobile-nav"
            onClick={() => setOpen((value) => !value)}
          >
            {open ? 'Закрыть' : 'Меню'}
          </button>
        </div>
      </div>

      {open ? (
        <nav id="mobile-nav" className="border-t border-white/10 bg-brand-reference-panelDeep px-4 py-3 sm:px-5 sm:py-4 lg:hidden" aria-label="Мобильная навигация">
          <div className="mx-auto grid max-w-[1534px] gap-1 text-base text-brand-reference-muted">
            {navigation.map(([label, href]) =>
              href ? (
                <NavLink
                  key={label}
                  to={href}
                  onClick={() => setOpen(false)}
                  className={({ isActive }) =>
                    `rounded-[5px] px-3 py-2.5 transition-colors hover:bg-white/5 hover:text-white focus:bg-white/5 focus:text-white ${isActive ? 'bg-white/5 text-white' : ''}`
                  }
                >
                  {label}
                </NavLink>
              ) : (
                <span key={label} aria-disabled="true" className="px-3 py-2.5 text-brand-reference-muted/45">
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
