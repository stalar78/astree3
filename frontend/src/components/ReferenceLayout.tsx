import { useEffect, useState, type ReactNode } from 'react';

import { isHostingEdition } from '../config/edition';
import { listPublicEvents, type PublicEvent, type PublicEventType } from '../publicContent/publicContentApi';

const MONTHS_TO_SHOW = 5;
const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
const SYMBOLS = [
  '/brand/symbols/symbol-01.png',
  '/brand/symbols/symbol-02.png',
  '/brand/symbols/symbol-03.png',
  '/brand/symbols/symbol-04.png',
  '/brand/symbols/symbol-05.png',
];
const UPCOMING_DATE = new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: 'long' });

export function ReferenceLayout({ children }: { children: ReactNode }) {
  const { events, state } = useHostingEvents();

  return (
    <div className="mx-auto grid w-full max-w-[1534px] gap-6 px-4 py-6 sm:px-5 sm:py-8 lg:px-8 xl:grid-cols-[128px_minmax(0,1fr)_220px] xl:gap-8 xl:py-9">
      <SymbolRail />
      <div className="min-w-0">
        {children}
        {isHostingEdition ? <UpcomingEvents events={events} state={state} /> : null}
      </div>
      <CalendarRail events={events} />
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
            className="flex aspect-square items-center justify-center rounded-[6px] border border-brand-reference-line/45 bg-brand-reference-panelDeep p-[8%] shadow-symbolCard"
            aria-hidden="true"
          >
            <img src={src} alt="" className="h-full w-full object-contain" />
          </div>
        ))}
      </div>
    </aside>
  );
}

function CalendarRail({ events }: { events: PublicEvent[] }) {
  const now = new Date();
  const eventsByDate = new Map<string, PublicEvent[]>();

  for (const event of events) {
    const existing = eventsByDate.get(event.event_date) ?? [];
    existing.push(event);
    eventsByDate.set(event.event_date, existing);
  }

  return (
    <aside className="hidden xl:block" aria-label="Календарь">
      <div className="space-y-8 pt-10">
        {Array.from({ length: MONTHS_TO_SHOW }, (_, index) => {
          const date = new Date(now.getFullYear(), now.getMonth() + index, 1);
          return <MonthCalendar key={`${date.getFullYear()}-${date.getMonth()}`} date={date} today={now} eventsByDate={eventsByDate} />;
        })}
      </div>
    </aside>
  );
}

function MonthCalendar({
  date,
  today,
  eventsByDate,
}: {
  date: Date;
  today: Date;
  eventsByDate: Map<string, PublicEvent[]>;
}) {
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
          if (!day) return <span key={index} />;

          const dateKey = localDateKey(new Date(year, month, day));
          const dayEvents = eventsByDate.get(dateKey) ?? [];
          const isToday = isCurrentMonth && day === today.getDate();
          const hasEvent = dayEvents.length > 0;
          const eventLabel = hasEvent ? `События: ${dayEvents.map((event) => event.title).join(', ')}` : undefined;

          return (
            <span
              key={index}
              className={`relative mx-auto flex h-6 w-7 items-center justify-center rounded-sm ${isToday ? 'border border-brand-reference-line/80 bg-white/5 shadow-calendarToday' : ''} ${hasEvent ? 'font-semibold' : ''}`}
              aria-current={isToday ? 'date' : undefined}
              aria-label={eventLabel ? `${day}. ${eventLabel}` : undefined}
              title={eventLabel}
            >
              {day}
              {hasEvent ? <span className="absolute -bottom-1 h-1 w-1 rounded-full bg-brand-reference-red" aria-hidden="true" /> : null}
            </span>
          );
        })}
      </div>
    </section>
  );
}

function UpcomingEvents({ events, state }: { events: PublicEvent[]; state: 'idle' | 'loading' | 'ready' | 'error' }) {
  return (
    <section className="mt-6 rounded-[6px] border border-brand-reference-line/30 bg-brand-reference-panel px-5 py-5 shadow-referenceCard sm:mt-8 sm:px-6 sm:py-6 xl:hidden" aria-labelledby="upcoming-events-title">
      <p className="text-xs uppercase tracking-[0.14em] text-brand-reference-muted/55">Календарь</p>
      <h2 id="upcoming-events-title" className="mt-2 font-referenceHeading text-[clamp(1.45rem,5vw,1.9rem)] font-normal text-brand-reference-text">
        Ближайшие события
      </h2>
      <div className="my-4 h-px bg-brand-reference-line/65" />

      {state === 'loading' ? <p className="text-[15px] font-light leading-7 text-brand-reference-muted">Календарь загружается.</p> : null}
      {state === 'error' ? <p className="text-[15px] font-light leading-7 text-brand-reference-muted">Календарь временно недоступен.</p> : null}
      {state === 'ready' && events.length === 0 ? (
        <p className="text-[15px] font-light leading-7 text-brand-reference-muted">Ближайшие публичные даты пока не опубликованы.</p>
      ) : null}

      {state === 'ready' && events.length > 0 ? (
        <div className="grid gap-4">
          {events.slice(0, 5).map((event) => (
            <article key={event.id} className="border-l-2 border-brand-reference-red pl-4">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs uppercase tracking-[0.1em] text-brand-reference-muted/60">
                <time dateTime={event.event_date}>{UPCOMING_DATE.format(parsePublicDate(event.event_date))}</time>
                <span>{eventTypeLabel(event.event_type)}</span>
              </div>
              <h3 className="mt-1 font-referenceHeading text-xl font-normal text-brand-reference-text">{event.title}</h3>
              {event.note ? <p className="mt-2 text-[15px] font-light leading-7 text-brand-reference-muted">{event.note}</p> : null}
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function useHostingEvents(): { events: PublicEvent[]; state: 'idle' | 'loading' | 'ready' | 'error' } {
  const [events, setEvents] = useState<PublicEvent[]>([]);
  const [state, setState] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');

  useEffect(() => {
    if (!isHostingEdition) return;

    const controller = new AbortController();
    const now = new Date();
    const end = new Date(now.getFullYear(), now.getMonth() + MONTHS_TO_SHOW, 0);
    setState('loading');

    void listPublicEvents({ from: localDateKey(now), to: localDateKey(end) }, controller.signal)
      .then((items) => {
        setEvents(items);
        setState('ready');
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        setEvents([]);
        setState('error');
      });

    return () => controller.abort();
  }, []);

  return { events, state };
}

function localDateKey(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function parsePublicDate(value: string): Date {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(year, month - 1, day);
}

function eventTypeLabel(type: PublicEventType): string {
  switch (type) {
    case 'work':
      return 'Работа ложи';
    case 'feast':
      return 'Праздник';
    case 'other':
      return 'Событие';
  }
}
