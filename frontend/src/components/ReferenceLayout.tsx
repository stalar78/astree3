import type { ReactNode } from 'react';

const MONTHS_TO_SHOW = 5;
const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

export function ReferenceLayout({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto grid w-full max-w-[1534px] gap-8 px-5 py-8 lg:px-8 xl:grid-cols-[128px_minmax(0,1fr)_220px] xl:py-10">
      <SymbolRail />
      <div className="min-w-0">{children}</div>
      <CalendarRail />
    </div>
  );
}

function SymbolRail() {
  return (
    <aside className="hidden xl:block" aria-label="Символическая навигационная колонка">
      <div className="grid gap-5 pt-1">
        {Array.from({ length: 5 }, (_, index) => (
          <div
            key={index}
            className="flex aspect-square items-center justify-center rounded-sm border border-white/10 bg-brand-reference-panel shadow-referenceCard"
            aria-hidden="true"
          >
            <PlaceholderGlyph variant={index} />
          </div>
        ))}
      </div>
      <p className="mt-4 text-center text-[10px] uppercase tracking-[0.12em] text-brand-reference-muted/45">Временные символы</p>
    </aside>
  );
}

function PlaceholderGlyph({ variant }: { variant: number }) {
  const paths = [
    <g key="column-a"><path d="M18 18h44M22 18v9h36v-9M27 29v29M38 29v29M49 29v29M60 29v29M20 62h40" /><path d="M23 28h34" /></g>,
    <g key="column-b"><path d="M17 22h46l-5 8H22zM24 31h32l-4 28H28zM22 62h36" /><path d="M31 35v20M40 35v20M49 35v20" /></g>,
    <g key="scroll"><circle cx="25" cy="31" r="10" /><circle cx="55" cy="31" r="10" /><path d="M25 21h30M25 41h30M25 41v22M55 41v22" /></g>,
    <g key="tools"><path d="M24 18v45M19 18h10M20 28h8M47 19v44M43 19h8M40 28h14" /><path d="M18 63h12M41 63h12" /></g>,
    <g key="triangle"><path d="M40 13 67 62H13zM40 26v25M32 40h16" /><path d="M28 52h24" /></g>,
  ];

  return (
    <svg viewBox="0 0 80 80" className="h-16 w-16 text-brand-reference-muted/75" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      {paths[variant]}
    </svg>
  );
}

function CalendarRail() {
  const now = new Date();

  return (
    <aside className="hidden xl:block" aria-label="Календарь">
      <div className="space-y-8 pt-1">
        {Array.from({ length: MONTHS_TO_SHOW }, (_, index) => {
          const date = new Date(now.getFullYear(), now.getMonth() + index, 1);
          return <MonthCalendar key={`${date.getFullYear()}-${date.getMonth()}`} date={date} today={now} />;
        })}
      </div>
    </aside>
  );
}

function MonthCalendar({ date, today }: { date: Date; today: Date }) {
  const year = date.getFullYear();
  const month = date.getMonth();
  const monthLabel = new Intl.DateTimeFormat('ru-RU', { month: 'long' }).format(date);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayOffset = (new Date(year, month, 1).getDay() + 6) % 7;
  const cells = Array.from({ length: firstDayOffset + daysInMonth }, (_, index) => (index < firstDayOffset ? null : index - firstDayOffset + 1));

  const isCurrentMonth = year === today.getFullYear() && month === today.getMonth();

  return (
    <section>
      <h2 className="mb-2 text-center text-[17px] font-light capitalize text-brand-reference-muted">{monthLabel}</h2>
      <div className="grid grid-cols-7 gap-y-1 text-center text-[13px] leading-5 text-brand-reference-muted/55" aria-hidden="true">
        {WEEKDAYS.map((weekday) => <span key={weekday}>{weekday.slice(0, 1)}</span>)}
      </div>
      <div className="mt-1 grid grid-cols-7 gap-y-1 text-center text-[16px] leading-6 text-brand-reference-text/90">
        {cells.map((day, index) => {
          const isToday = isCurrentMonth && day === today.getDate();
          return (
            <span
              key={index}
              className={day ? `mx-auto flex h-6 w-7 items-center justify-center rounded-sm ${isToday ? 'border border-brand-reference-line bg-white/5' : ''}` : ''}
              aria-current={isToday ? 'date' : undefined}
            >
              {day ?? ''}
            </span>
          );
        })}
      </div>
    </section>
  );
}
