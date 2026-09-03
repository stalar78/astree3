export function SiteFooter() {
  return (
    <footer className="relative bg-brand-reference-footer text-brand-reference-text">
      <div aria-hidden="true" className="relative">
        <div className="h-[4px] bg-white" />
        <div className="h-[4px] bg-brand-reference-flagBlue" />
        <div className="h-[4px] bg-brand-reference-flagRed" />
        <img
          className="absolute left-1/2 top-[32px] z-20 h-24 w-24 -translate-x-1/2 -translate-y-1/2 object-contain drop-shadow-[0_8px_14px_rgba(0,0,0,0.4)] sm:top-[34px] sm:h-[112px] sm:w-[112px] lg:h-[132px] lg:w-[132px]"
          src="/brand/grand-lodge-russia-emblem.png"
          alt=""
        />
      </div>

      <div className="mx-auto max-w-[1534px] px-4 pb-8 pt-[76px] text-center sm:px-5 sm:pb-9 sm:pt-[80px] lg:px-8 lg:pb-10 lg:pt-[76px]">
        <div className="mx-auto max-w-5xl space-y-1.5 text-[clamp(0.92rem,4vw,1.08rem)] font-light leading-snug text-brand-reference-text/90 sm:text-[clamp(1rem,2.4vw,1.18rem)] lg:text-[clamp(1rem,1.45vw,1.28rem)] lg:leading-tight">
          <div className="space-y-1 sm:hidden">
            <p>127287 Полтавская ул. д. 18</p>
            <p>Москва, Россия · +7 495 611 30 11</p>
          </div>
          <div className="hidden grid-cols-[1fr_118px_1fr] items-center gap-2 sm:grid lg:grid-cols-[1fr_138px_1fr]">
            <p className="text-right">127287 Полтавская ул. д. 18</p>
            <span aria-hidden="true" />
            <p className="text-left">Москва, Россия · +7 495 611 30 11</p>
          </div>
          <p className="break-words">
            <a className="transition-colors hover:text-white" href="mailto:grandlodge@russianmasonry.ru">grandlodge@russianmasonry.ru</a>
          </p>
          <p>Пн – Пт 10.00 – 18.00</p>
        </div>
      </div>
    </footer>
  );
}
