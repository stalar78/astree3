import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ADMIN_CANDIDATE_PAGE_SIZE,
  ADMIN_CANDIDATE_STATUSES,
  type AdminCandidateListItem,
  type AdminCandidateStatus,
  listAdminCandidates,
  AdminApiError,
} from '../../admin/adminApi';
import { formatAdminError } from '../../admin/adminMessages';
import { AdminStatusPill } from '../../admin/AdminStatusPill';
import { ADMIN_CANDIDATE_STATUS_LABELS } from '../../admin/adminStatus';

const DATE_FORMAT = new Intl.DateTimeFormat('ru-RU', {
  dateStyle: 'medium',
  timeStyle: 'short',
});

export function AdminCandidatesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [items, setItems] = useState<AdminCandidateListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);
  const [canNext, setCanNext] = useState(false);
  const [retryIndex, setRetryIndex] = useState(0);

  const rawStatus = searchParams.get('status') ?? '';
  const statusIsValid = isAdminCandidateStatus(rawStatus);
  const status = statusIsValid ? rawStatus : '';
  const rawOffset = searchParams.get('offset');
  const offsetIsValid = isNonNegativeInteger(rawOffset);
  const offset = offsetIsValid ? Number(rawOffset) : 0;

  useEffect(() => {
    document.title = 'Кандидаты | Astrea Admin';
  }, []);

  useEffect(() => {
    if ((rawStatus && !statusIsValid) || (rawOffset !== null && !offsetIsValid)) {
      setSearchParams(buildSearchParams(status, 0), { replace: true });
    }
  }, [offsetIsValid, rawOffset, rawStatus, setSearchParams, status, statusIsValid]);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setLoading(true);
    setError(null);
    setErrorStatus(null);

    void listAdminCandidates({ status, limit: ADMIN_CANDIDATE_PAGE_SIZE, offset }, controller.signal)
      .then((response) => {
        if (!active) {
          return;
        }
        setItems(response.items);
        setCanNext(response.items.length === ADMIN_CANDIDATE_PAGE_SIZE);
      })
      .catch((caughtError: unknown) => {
        if (!active || controller.signal.aborted) {
          return;
        }
        if (caughtError instanceof AdminApiError && (caughtError.status === 401 || caughtError.status === 403)) {
          navigate('/admin/login', { replace: true, state: { from: `${location.pathname}${location.search}` } });
          return;
        }
        setItems([]);
        setCanNext(false);
        setError(formatAdminError(caughtError, 'list'));
        setErrorStatus(caughtError instanceof AdminApiError ? caughtError.status : null);
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [location.pathname, location.search, navigate, offset, retryIndex, status]);

  const emptyMessage = status ? 'Заявок с таким статусом нет.' : 'Заявок пока нет.';
  const retryable = errorStatus === null || errorStatus === 503;

  return (
    <div className="space-y-8">
      <section className="rounded-3xl border border-brand-gray10/20 bg-white p-6 shadow-formal">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-brand-red">Candidate administration</p>
            <h2 className="mt-3 font-display text-5xl">Заявки</h2>
          </div>
          <label className="grid gap-2 text-sm font-semibold uppercase tracking-[0.12em]">
            Фильтр по статусу
            <select
              className="rounded-2xl border border-brand-gray10/20 bg-brand-paper px-4 py-3 text-base outline-none transition focus:border-brand-red"
              value={status}
              onChange={(event) => {
                setSearchParams(buildSearchParams(event.target.value, 0));
              }}
            >
              <option value="">Все статусы</option>
              {ADMIN_CANDIDATE_STATUSES.map((candidateStatus) => (
                <option key={candidateStatus} value={candidateStatus}>
                  {ADMIN_CANDIDATE_STATUS_LABELS[candidateStatus]}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="mt-6 flex flex-wrap gap-3">
          <FilterChip active={!status} onClick={() => setSearchParams(buildSearchParams('', 0))}>
            Все
          </FilterChip>
          {ADMIN_CANDIDATE_STATUSES.map((candidateStatus) => (
            <FilterChip key={candidateStatus} active={status === candidateStatus} onClick={() => setSearchParams(buildSearchParams(candidateStatus, 0))}>
              {ADMIN_CANDIDATE_STATUS_LABELS[candidateStatus]}
            </FilterChip>
          ))}
        </div>
        {error ? (
          <div className="mt-6 flex flex-col gap-4">
            <Notice>{error}</Notice>
            {retryable ? (
              <div>
                <button
                  type="button"
                  className="rounded-full border border-brand-red bg-brand-red px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.14em] text-white transition hover:bg-transparent hover:text-brand-red"
                  onClick={() => setRetryIndex((value) => value + 1)}
                >
                  Повторить
                </button>
              </div>
            ) : null}
          </div>
        ) : null}
      </section>

      <section className="rounded-3xl border border-brand-gray10/20 bg-white shadow-formal">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-brand-gray10/10 px-6 py-4 text-sm uppercase tracking-[0.14em] text-brand-ink/60">
          <span>{loading ? 'Загрузка...' : 'Список заявок'}</span>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              className="rounded-full border border-brand-gray10/20 px-4 py-2 text-sm uppercase tracking-[0.12em] transition hover:border-brand-red hover:text-brand-red disabled:cursor-not-allowed disabled:opacity-40"
              disabled={offset === 0 || loading}
              onClick={() => setSearchParams(buildSearchParams(status, Math.max(0, offset - ADMIN_CANDIDATE_PAGE_SIZE)))}
            >
              Назад
            </button>
            <button
              type="button"
              className="rounded-full border border-brand-gray10/20 px-4 py-2 text-sm uppercase tracking-[0.12em] transition hover:border-brand-red hover:text-brand-red disabled:cursor-not-allowed disabled:opacity-40"
              disabled={!canNext || loading}
              onClick={() => setSearchParams(buildSearchParams(status, offset + ADMIN_CANDIDATE_PAGE_SIZE))}
            >
              Далее
            </button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-brand-gray10/10">
            <thead className="bg-brand-paperAlt text-left text-xs uppercase tracking-[0.14em] text-brand-ink/60">
              <tr>
                <th className="px-6 py-4 font-semibold">Кандидат</th>
                <th className="px-6 py-4 font-semibold">Контакты</th>
                <th className="px-6 py-4 font-semibold">Статус</th>
                <th className="px-6 py-4 font-semibold">Фото</th>
                <th className="px-6 py-4 font-semibold">Обновлено</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-gray10/10">
              {loading ? (
                <tr>
                  <td className="px-6 py-10 text-sm text-brand-ink/60" colSpan={5}>
                    Загрузка списка...
                  </td>
                </tr>
              ) : error ? null : items.length === 0 ? (
                <tr>
                  <td className="px-6 py-10 text-sm text-brand-ink/60" colSpan={5}>
                    {emptyMessage}
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id} className="align-top hover:bg-brand-paper/60">
                    <td className="px-6 py-5">
                      <Link to={`/admin/candidates/${item.id}`} className="font-semibold text-brand-black transition hover:text-brand-red">
                        {item.full_name ?? `Кандидат #${item.id}`}
                      </Link>
                      <p className="mt-1 text-xs uppercase tracking-[0.14em] text-brand-ink/50">ID {item.id}</p>
                    </td>
                    <td className="px-6 py-5 text-sm leading-6 text-brand-ink/80">
                      <p>{item.city ?? '—'}</p>
                      <p>{item.email ?? '—'}</p>
                      <p>{item.phone ?? '—'}</p>
                    </td>
                    <td className="px-6 py-5">
                      <AdminStatusPill status={item.status} />
                    </td>
                    <td className="px-6 py-5 text-sm text-brand-ink/80">{item.has_photo ? 'Есть' : 'Нет'}</td>
                    <td className="px-6 py-5 text-sm text-brand-ink/80">{DATE_FORMAT.format(new Date(item.updated_at))}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function isAdminCandidateStatus(value: string): value is AdminCandidateStatus {
  return (ADMIN_CANDIDATE_STATUSES as readonly string[]).includes(value);
}

function isNonNegativeInteger(value: string | null): value is string {
  return value !== null && /^\d+$/.test(value);
}

function buildSearchParams(status: string, offset: number) {
  const next = new URLSearchParams();
  if (status) {
    next.set('status', status);
  }
  next.set('offset', String(offset));
  return next;
}

function FilterChip({ active, onClick, children }: { active: boolean; onClick: () => void; children: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-4 py-2 text-sm uppercase tracking-[0.12em] transition ${
        active ? 'border-brand-red bg-brand-red text-white' : 'border-brand-gray10/20 bg-brand-paper text-brand-ink hover:border-brand-red hover:text-brand-red'
      }`}
    >
      {children}
    </button>
  );
}

function Notice({ children }: { children: string }) {
  return <p className="rounded-2xl border border-brand-red/20 bg-brand-red/10 px-4 py-3 text-sm leading-6 text-brand-ink">{children}</p>;
}
