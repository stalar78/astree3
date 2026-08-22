import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import {
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
  const navigate = useNavigate();
  const [items, setItems] = useState<AdminCandidateListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const statusParam = searchParams.get('status') ?? '';
  const activeStatus = isAdminCandidateStatus(statusParam) ? statusParam : '';

  useEffect(() => {
    document.title = 'Кандидаты | Astrea Admin';
  }, []);

  useEffect(() => {
    if (statusParam && !activeStatus) {
      setLoading(false);
      setItems([]);
      setError('Запрос не прошёл проверку.');
      return;
    }

    const controller = new AbortController();
    let active = true;
    setLoading(true);
    setError(null);

    void listAdminCandidates({ status: activeStatus, limit: 50, offset: 0 }, controller.signal)
      .then((response) => {
        if (active) {
          setItems(response.items);
        }
      })
      .catch((caughtError: unknown) => {
        if (!active || controller.signal.aborted) {
          return;
        }
        if (caughtError instanceof AdminApiError && (caughtError.status === 401 || caughtError.status === 403)) {
          navigate('/admin/login', { replace: true, state: { from: '/admin/candidates' } });
          return;
        }
        setError(formatAdminError(caughtError, 'list'));
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
  }, [activeStatus, navigate, statusParam]);

  return (
    <div className="space-y-8">
      <section className="rounded-3xl border border-brand-gray10/20 bg-white/90 p-6 shadow-formal">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-brand-red">Candidate administration</p>
            <h2 className="mt-3 font-display text-5xl">Заявки</h2>
          </div>
          <label className="grid gap-2 text-sm font-semibold uppercase tracking-[0.12em]">
            Фильтр по статусу
            <select
              className="rounded-2xl border border-brand-gray10/20 bg-brand-paper px-4 py-3 text-base outline-none transition focus:border-brand-red"
              value={activeStatus}
              onChange={(event) => {
                const nextStatus = event.target.value;
                setSearchParams(nextStatus ? { status: nextStatus } : {});
              }}
            >
              <option value="">Все статусы</option>
              {ADMIN_CANDIDATE_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {ADMIN_CANDIDATE_STATUS_LABELS[status]}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="mt-6 flex flex-wrap gap-3">
          <FilterChip active={!activeStatus} onClick={() => setSearchParams({})}>
            Все
          </FilterChip>
          {ADMIN_CANDIDATE_STATUSES.map((status) => (
            <FilterChip key={status} active={activeStatus === status} onClick={() => setSearchParams({ status })}>
              {ADMIN_CANDIDATE_STATUS_LABELS[status]}
            </FilterChip>
          ))}
        </div>
        {error ? <Notice className="mt-6">{error}</Notice> : null}
      </section>

      <section className="rounded-3xl border border-brand-gray10/20 bg-white shadow-formal">
        <div className="border-b border-brand-gray10/10 px-6 py-4 text-sm uppercase tracking-[0.14em] text-brand-ink/60">
          {loading ? 'Загрузка...' : `${items.length} записей`}
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
              ) : items.length === 0 ? (
                <tr>
                  <td className="px-6 py-10 text-sm text-brand-ink/60" colSpan={5}>
                    Записей нет.
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

function Notice({ children, className = '' }: { children: string; className?: string }) {
  return <p className={`rounded-2xl border border-brand-red/20 bg-brand-red/10 px-4 py-3 text-sm leading-6 text-brand-ink ${className}`}>{children}</p>;
}
