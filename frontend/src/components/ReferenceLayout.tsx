import type { ReactNode } from 'react';

const MONTHS_TO_SHOW = 5;
const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
const SYMBOLS = [
  '/brand/symbols/symbol-01.png',
  '/brand/symbols/symbol-02.png',
  '/brand/symbols/symbol-03.png',
  '/brand/symbols/symbol-04.png',
  '/brand/symbols/symbol-05.png',
];

export function ReferenceLayout({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto grid w-full max-w-[1534px] gap-8 px-5 py-8 lg:px-8 xl:grid-cols-[128px_minmax(0,1fr)_220px] xl:py-9">
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
        {SYMBOLS.map((src) => (
          <div
            key={src}
            className="flex aspect-square items-center justify-center rounded-sm border border-brand-reference-line/35 bg-brand-reference-panelDeep p-[18%] shadow-symbolCard"
            aria-hidden="true"
          >
            <img src={src} alt="" className="h-full w-full object-contain" />
          </div>
        ))}
      </div>
    </aside>
  );
}

function CalendarRail() {
  const now = new Date();

  return (
    <aside className="hidden xl:block" aria-label="Календарь">
      <div className="space-y-8 pt-[86px]">
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
      <h2 className="mb-2 text-center text-[18px] font-light capitalize text-brand-reference-muted">{monthLabel}</h2>
      <div className="grid grid-cols-7 gap-y-1 text-center text-[13px] leading-5 text-brand-reference-muted/55" aria-hidden="true">
        {WEEKDAYS.map((weekday) => <span key={weekday}>{weekday.slice(0, 1)}</span>)}
      </div>
      <div className="mt-1 grid grid-cols-7 gap-y-1 text-center text-[17px] leading-6 text-brand-reference-text/90">
        {cells.map((day, index) => {
          const isToday = isCurrentMonth && day === today.getDate();
          return (
            <span
              key={index}
              className={day ? `mx-auto flex h-6 w-7 items-center justify-center rounded-sm ${isToday ? 'border border-brand-reference-line/80 bg-white/5 shadow-calendarToday' : ''}` : ''}
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
