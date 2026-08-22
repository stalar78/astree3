import { Link } from 'react-router-dom';
import { OrnamentDivider } from './OrnamentDivider';

export function SiteFooter() {
  return (
    <footer className="bg-brand-black text-white">
      <div className="mx-auto max-w-7xl px-5 py-14 lg:px-8">
        <OrnamentDivider tone="dark" />
        <div className="grid gap-10 py-10 md:grid-cols-[1fr_auto_1fr] md:items-center">
          <div>
            <p className="font-display text-2xl">Д.Л. «Астрея» № 3</p>
            <p className="mt-2 max-w-sm text-sm leading-6 text-brand-gray6">Официальный сайт. Публичные материалы и правовые тексты публикуются после утверждения.</p>
          </div>
          <img className="mx-auto h-28 w-28 object-contain" src="/brand/astrea-seal.png" alt="Печать Достопочтенной Ложи «Астрея» № 3" />
          <nav className="grid gap-2 text-sm text-brand-gray6 md:justify-end md:text-right" aria-label="Нижняя навигация">
            <Link to="/privacy" className="hover:text-white">Политика конфиденциальности</Link>
            <Link to="/consent" className="hover:text-white">Согласие на обработку данных</Link>
            <Link to="/kontakty" className="hover:text-white">Контакты</Link>
          </nav>
        </div>
        <p className="border-t border-white/10 pt-6 text-xs uppercase text-brand-gray10">MDCCLXXV</p>
      </div>
    </footer>
  );
}
