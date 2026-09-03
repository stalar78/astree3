export function SiteFooter() {
  return (
    <footer className="bg-[#293144] text-brand-reference-text">
      <div aria-hidden="true">
        <div className="h-[8px] bg-brand-reference-white" />
        <div className="h-[7px] bg-brand-reference-red" />
      </div>

      <div className="mx-auto max-w-[1534px] px-5 py-9 text-center lg:px-8 lg:py-11">
        <img
          className="mx-auto h-20 w-20 object-contain lg:h-24 lg:w-24"
          src="/brand/grand-lodge-russia-emblem.png"
          alt="Эмблема Великой Ложи России"
        />
        <div className="mx-auto mt-3 max-w-4xl space-y-1 text-[clamp(1rem,1.7vw,1.45rem)] font-light leading-tight text-brand-reference-text/90">
          <p>127287 Полтавская ул. д. 18 · Москва, Россия · +7 495 611 30 11</p>
          <p>
            <a className="transition-colors hover:text-white" href="mailto:grandlodge@russianmasonry.ru">grandlodge@russianmasonry.ru</a>
          </p>
          <p>Пн – Пт 10.00 – 18.00</p>
        </div>
      </div>
    </footer>
  );
}
