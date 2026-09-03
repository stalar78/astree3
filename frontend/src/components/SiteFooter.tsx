export function SiteFooter() {
  return (
    <footer className="relative bg-brand-reference-footer text-brand-reference-text">
      <div aria-hidden="true" className="relative">
        <div className="h-[9px] bg-white" />
        <div className="h-[3px] bg-brand-reference-flagBlue" />
        <div className="h-[6px] bg-brand-reference-flagRed" />
        <img
          className="absolute left-1/2 top-1/2 z-20 h-[92px] w-[92px] -translate-x-1/2 -translate-y-1/2 object-contain drop-shadow-[0_8px_14px_rgba(0,0,0,0.4)] lg:h-[104px] lg:w-[104px]"
          src="/brand/grand-lodge-russia-emblem.png"
          alt=""
        />
      </div>

      <div className="mx-auto max-w-[1534px] px-5 pb-9 pt-[58px] text-center lg:px-8 lg:pb-10 lg:pt-[64px]">
        <div className="mx-auto max-w-4xl space-y-1 text-[clamp(1rem,1.45vw,1.28rem)] font-light leading-tight text-brand-reference-text/90">
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
