import { Link } from 'react-router-dom';
import { OrnamentDivider } from './OrnamentDivider';

export function SiteFooter() {
  return (
    <footer className="bg-brand-black text-white">
      <div className="mx-auto max-w-7xl px-5 py-16 text-center lg:px-8 lg:py-24">
        <img className="mx-auto h-auto w-44 max-w-[70vw] object-contain md:w-60" src="/brand/astrea-seal.png" alt="Печать Достопочтенной Ложи «Астрея» № 3" />
        <p className="mt-8 font-display text-4xl">Достопочтенная Ложа «Астрея» № 3</p>
        <p className="mt-3 text-sm uppercase text-brand-gray6">на Востоке Санкт-Петербурга</p>
        <div className="my-10">
          <OrnamentDivider tone="dark" />
        </div>
        <div className="grid gap-10 text-left md:grid-cols-3">
          <FooterColumn title="Разделы" links={[['О ложе', '/o-lozhe'], ['Цели и принципы', '/celi-i-principy'], ['Новости', '/novosti'], ['Видео', '/video'], ['Кандидатам', '/vstuplenie']]} />
          <FooterColumn title="Справка" links={[['Ложи Санкт-Петербурга', '/lozhi-sankt-peterburga'], ['Частые вопросы', '/faq'], ['Политика конфиденциальности', '/privacy'], ['Согласие на обработку данных', '/consent']]} />
          <div>
            <p className="font-display text-2xl">Контакты</p>
            <p className="mt-4 text-sm leading-6 text-brand-gray6">Контактная информация готовится к публикации.</p>
            <p className="mt-4 text-sm uppercase text-brand-gray6">Санкт-Петербург</p>
          </div>
        </div>
        <div className="mt-12 flex flex-col gap-3 border-t border-white/10 pt-6 text-xs uppercase text-brand-gray10 md:flex-row md:justify-between">
          <p>© {new Date().getFullYear()} Д.·.Л.·. «Астрея» № 3</p>
          <p>MDCCLXXV</p>
        </div>
      </div>
    </footer>
  );
}

function FooterColumn({ title, links }: { title: string; links: [string, string][] }) {
  return (
    <nav aria-label={title}>
      <p className="font-display text-2xl">{title}</p>
      <div className="mt-4 grid gap-2 text-sm text-brand-gray6">
        {links.map(([label, href]) => (
          <Link key={href} to={href} className="hover:text-white">
            {label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
