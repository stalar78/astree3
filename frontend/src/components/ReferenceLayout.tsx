import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react';

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
// Awaiting client-confirmed dates; do not infer them from general calendars.
const PENDING_IOANN_DATES = {
  summerIoann: null,
  winterIoann: null,
} satisfies Record<string, string | null>;
const VACATION_MONTHS = new Set([6, 7]);

export function ReferenceLayout({ children }: { children: ReactNode }) {
  const { events, state } = useHostingEvents();

  return (
    <div className="mx-auto grid w-full max-w-[1280px] gap-6 px-4 py-6 sm:px-5 sm:py-8 lg:px-7 xl:grid-cols-[108px_minmax(0,1fr)_188px] xl:gap-7 xl:py-7">
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
  const [dialogOpen, setDialogOpen] = useState(false);
  const [password, setPassword] = useState('');
  const [accessFeedback, setAccessFeedback] = useState<string | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const passwordRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (!dialogOpen) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setDialogOpen(false);
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [dialogOpen]);

  useEffect(() => {
    if (!dialogOpen) {
      triggerRef.current?.focus();
      return;
    }

    passwordRef.current?.focus();
  }, [dialogOpen]);

  function openDialog(trigger: HTMLButtonElement) {
    triggerRef.current = trigger;
    setPassword('');
    setAccessFeedback(null);
    setDialogOpen(true);
  }

  function handleAccessSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!password.trim()) {
      setAccessFeedback('Введите пароль.');
      passwordRef.current?.focus();
      return;
    }

    setAccessFeedback('Доступ к разделу не предоставлен.');
  }

  return (
    <>
      <aside className="hidden xl:block" aria-label="Символическая навигационная колонка">
        <div className="grid gap-4 pt-1">
          {SYMBOLS.map((src, index) => (
            <button
              key={src}
              type="button"
              className="astrea-symbol-button flex aspect-square items-center justify-center rounded-[5px] border border-brand-reference-line/45 bg-brand-reference-panelDeep p-[8%] shadow-symbolCard transition-[background-color,border-color,box-shadow] focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-white/70"
              aria-haspopup="dialog"
              aria-label={`Открыть закрытый раздел ${index + 1}`}
              onClick={(event) => openDialog(event.currentTarget)}
            >
              <img src={src} alt="" className="h-full w-full object-contain transition-[filter]" />
            </button>
          ))}
        </div>
      </aside>

      {dialogOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 px-4 py-6" role="presentation" onMouseDown={() => setDialogOpen(false)}>
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="symbol-dialog-title"
            className="w-full max-w-sm rounded-[6px] border border-brand-reference-line/45 bg-brand-reference-panel px-5 py-5 text-brand-reference-text shadow-referenceCard"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <h2 id="symbol-dialog-title" className="font-referenceHeading text-2xl font-medium">
              Закрытый раздел
            </h2>
            <p className="mt-3 text-[15px] font-light leading-7 text-brand-reference-muted">
              Введите пароль для доступа к разделу.
            </p>
            <form className="mt-4" onSubmit={handleAccessSubmit}>
              <label htmlFor="symbol-section-password" className="sr-only">
                Пароль
              </label>
              <input
                ref={passwordRef}
                id="symbol-section-password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  setAccessFeedback(null);
                }}
                className="w-full rounded-[5px] border border-brand-reference-line/65 bg-brand-reference-panelDeep px-4 py-3 text-base text-brand-reference-text outline-none transition focus:border-brand-reference-white focus:ring-1 focus:ring-brand-reference-white/20"
                placeholder="Пароль"
              />
              {accessFeedback ? (
                <p className="mt-3 text-sm font-light leading-6 text-brand-reference-muted" role="status" aria-live="polite">
                  {accessFeedback}
                </p>
              ) : null}
              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  type="submit"
                  className="inline-flex min-h-10 items-center justify-center rounded-[5px] border border-brand-reference-red bg-brand-reference-red px-4 py-2 text-sm font-medium uppercase tracking-[0.08em] text-white transition-colors hover:bg-transparent hover:text-brand-reference-text focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-brand-reference-red"
                >
                  Войти
                </button>
                <button
                  type="button"
                  className="inline-flex min-h-10 items-center justify-center rounded-[5px] border border-brand-reference-line/65 px-4 py-2 text-sm font-medium uppercase tracking-[0.08em] text-brand-reference-text transition-colors hover:border-brand-reference-white hover:text-white focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-brand-reference-line"
                  onClick={() => setDialogOpen(false)}
                >
                  Закрыть
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </>
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
      <div className="space-y-6 pt-8">
        {Array.from({ length: MONTHS_TO_SHOW }, (_, index) => {
          const date = new Date(now.getFullYear(), now.getMonth() + index, 1);
          return <MonthCalendar key={`${date.getFullYear()}-${date.getMonth()}`} date={date} today={now} eventsByDate={eventsByDate} />;
        })}
        {events.length > 0 ? (
          <p className="text-center text-[11px] font-light leading-5 text-brand-reference-muted/60">
            <span aria-hidden="true">●</span> опубликованное событие
          </p>
        ) : null}
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
  const vacationLabel = VACATION_MONTHS.has(month) ? 'Отпуск' : null;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayOffset = (new Date(year, month, 1).getDay() + 6) % 7;
  const cells = Array.from({ length: firstDayOffset + daysInMonth }, (_, index) => (index < firstDayOffset ? null : index - firstDayOffset + 1));

  const isCurrentMonth = year === today.getFullYear() && month === today.getMonth();

  return (
    <section>
      <h2 className="mb-2 text-center text-[16px] font-light capitalize text-brand-reference-muted">
        {monthLabel}
        {vacationLabel ? (
          <span className="ml-2 align-middle text-[10px] font-medium uppercase tracking-[0.12em] text-brand-reference-muted/65" title={vacationLabel}>
            {vacationLabel}
          </span>
        ) : null}
      </h2>
      <div className="grid grid-cols-7 gap-y-1 text-center text-[11px] leading-5 text-brand-reference-muted/55" aria-hidden="true">
        {WEEKDAYS.map((weekday) => <span key={weekday}>{weekday.slice(0, 1)}</span>)}
      </div>
      <div className="mt-1 grid grid-cols-7 gap-y-1 text-center text-[15px] leading-6 text-brand-reference-text/90">
        {cells.map((day, index) => {
          if (!day) return <span key={index} />;

          const dateKey = localDateKey(new Date(year, month, day));
          const dayEvents = eventsByDate.get(dateKey) ?? [];
          const specialNotes = getSpecialCalendarNotes(year, month, day);
          const isToday = isCurrentMonth && day === today.getDate();
          const hasEvent = dayEvents.length > 0;
          const labels = [
            ...dayEvents.map((event) => event.title),
            ...specialNotes.map((note) => note.label),
          ];
          const eventLabel = labels.length > 0 ? labels.join(', ') : undefined;
          const hasSecondSaturday = specialNotes.some((note) => note.kind === 'second-saturday');

          return (
            <span
              key={index}
              className={`relative mx-auto flex h-6 w-7 items-center justify-center rounded-sm outline-none focus-visible:ring-1 focus-visible:ring-brand-reference-white/40 ${isToday ? 'border border-brand-reference-line/80 bg-white/5 shadow-calendarToday' : ''} ${hasSecondSaturday ? 'border border-brand-reference-line/55 bg-brand-reference-line/10 shadow-calendarSpecial' : ''} ${hasEvent ? 'font-semibold' : ''}`}
              aria-current={isToday ? 'date' : undefined}
              aria-label={eventLabel ? `${day}. ${eventLabel}` : undefined}
              title={eventLabel}
              tabIndex={eventLabel ? 0 : undefined}
            >
              {day}
              {hasEvent ? <span className="absolute -bottom-1 h-1 w-1 rounded-full bg-brand-reference-red" aria-hidden="true" /> : null}
              {hasSecondSaturday ? <span className="absolute -right-0.5 top-0.5 h-1 w-1 rounded-full bg-brand-reference-line" aria-hidden="true" /> : null}
            </span>
          );
        })}
      </div>
    </section>
  );
}

type SpecialCalendarNote = {
  kind: 'second-saturday' | 'summer-ioann' | 'winter-ioann';
  label: string;
};

function getSpecialCalendarNotes(year: number, month: number, day: number): SpecialCalendarNote[] {
  const dateKey = localDateKey(new Date(year, month, day));
  const notes: SpecialCalendarNote[] = [];

  if (isSecondSaturday(year, month, day)) {
    notes.push({ kind: 'second-saturday', label: 'Собрание ложи' });
  }

  if (PENDING_IOANN_DATES.summerIoann === dateKey) {
    notes.push({ kind: 'summer-ioann', label: 'Летний Иоанн' });
  }

  if (PENDING_IOANN_DATES.winterIoann === dateKey) {
    notes.push({ kind: 'winter-ioann', label: 'Зимний Иоанн' });
  }

  return notes;
}

function isSecondSaturday(year: number, month: number, day: number): boolean {
  const current = new Date(year, month, day);
  if (current.getDay() !== 6) return false;
  return day > 7 && day <= 14;
}

function UpcomingEvents({ events, state }: { events: PublicEvent[]; state: 'idle' | 'loading' | 'ready' | 'error' }) {
  if (state === 'idle') return null;

  const todayKey = localDateKey(new Date());
  const upcoming = events.filter((event) => event.event_date >= todayKey).slice(0, 5);

  return (
    <section className="mt-6 rounded-[6px] border border-brand-reference-line/30 bg-brand-reference-panel px-5 py-5 shadow-referenceCard sm:mt-8 sm:px-6 sm:py-6 xl:hidden" aria-labelledby="upcoming-events-title">
      <p className="text-xs uppercase tracking-[0.14em] text-brand-reference-muted/55">Календарь</p>
      <h2 id="upcoming-events-title" className="mt-2 font-referenceHeading text-[clamp(1.45rem,5vw,1.9rem)] font-medium text-brand-reference-text">
        Ближайшие события
      </h2>
      <div className="my-4 h-px bg-brand-reference-line/65" />

      {state === 'loading' ? <p className="text-[15px] font-light leading-7 text-brand-reference-muted">Календарь загружается.</p> : null}
      {state === 'error' ? <p className="text-[15px] font-light leading-7 text-brand-reference-muted">Календарь временно недоступен.</p> : null}
      {state === 'ready' && upcoming.length === 0 ? (
        <p className="text-[15px] font-light leading-7 text-brand-reference-muted">Ближайшие публичные даты пока не опубликованы.</p>
      ) : null}

      {state === 'ready' && upcoming.length > 0 ? (
        <div className="grid gap-4">
          {upcoming.map((event) => (
            <article key={event.id} className="border-l-2 border-brand-reference-red pl-4">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs uppercase tracking-[0.1em] text-brand-reference-muted/60">
                <time dateTime={event.event_date}>{UPCOMING_DATE.format(parsePublicDate(event.event_date))}</time>
                <span>{eventTypeLabel(event.event_type)}</span>
              </div>
              <h3 className="mt-1 font-referenceHeading text-xl font-medium text-brand-reference-text">{event.title}</h3>
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
    const start = new Date(now.getFullYear(), now.getMonth(), 1);
    const end = new Date(now.getFullYear(), now.getMonth() + MONTHS_TO_SHOW, 0);
    setState('loading');

    void listPublicEvents({ from: localDateKey(start), to: localDateKey(end) }, controller.signal)
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
    default:
      return 'Событие';
  }
}
