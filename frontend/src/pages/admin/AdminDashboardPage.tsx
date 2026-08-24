import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AdminApiError, type AdminCandidateListItem, listAdminCandidates } from '../../admin/adminApi';
import { formatAdminError } from '../../admin/adminMessages';
import { AdminStatusPill } from '../../admin/AdminStatusPill';

const DATE_FORMAT = new Intl.DateTimeFormat('ru-RU', {
  dateStyle: 'medium',
  timeStyle: 'short',
});

const QUICK_LINKS = [
  {
    to: '/admin/candidates',
    eyebrow: 'Applications',
    title: 'Кандидаты',
    description: 'Заявки, статусы и защищённый просмотр данных кандидатов.',
  },
  {
    to: '/admin/news',
    eyebrow: 'Editorial',
    title: 'Новости',
    description: 'Создание, редактирование и публикация новостных материалов.',
  },
  {
    to: '/admin/videos',
    eyebrow: 'Media',
    title: 'Видео',
    description: 'Управление опубликованными внешними видеоматериалами.',
  },
  {
    to: '/admin/pages',
    eyebrow: 'Managed pages',
    title: 'Страницы',
    description: 'Редактирование разрешённых публичных страниц без изменения их ключей.',
  },
] as const;

export function AdminDashboardPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [items, setItems] = useState<AdminCandidateListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);
  const [retryIndex, setRetryIndex] = useState(0);

  useEffect(() => {
    document.title = 'Обзор | Astrea Admin';
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setLoading(true);
    setError(null);
    setErrorStatus(null);

    void listAdminCandidates({ limit: 5, offset: 0 }, controller.signal)
      .then((response) => {
        if (!active) return;
        setItems(response.items);
      })
      .catch((caughtError: unknown) => {
        if (!active || controller.signal.aborted) return;
        if (caughtError instanceof AdminApiError && (caughtError.status === 401 || caughtError.status === 403)) {
          navigate('/admin/login', { replace: true, state: { from: `${location.pathname}${location.search}` } });
          return;
        }
        setItems([]);
        setError(formatAdminError(caughtError, 'list'));
        setErrorStatus(caughtError instanceof AdminApiError ? caughtError.status : null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [location.pathname, location.search, navigate, retryIndex]);

  const retryable = errorStatus === null || errorStatus === 503;

  return (
    <div className="space-y-8">
      <section className="rounded-3xl border border-brand-gray10/20 bg-white p-6 shadow-formal lg:p-8">
        <p className="text-xs uppercase tracking-[0.24em] text-brand-red">Admin overview</p>
        <h2 className="mt-3 font-display text-5xl">Обзор</h2>
        <p className="mt-4 max-w-3xl text-base leading-7 text-brand-ink/70">
          Быстрый доступ к основным разделам администрирования и последним заявкам без дополнительных агрегатов или скрытых счётчиков.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" aria-label="Разделы администрирования">
        {QUICK_LINKS.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className="group flex min-h-56 flex-col justify-between rounded-3xl border border-brand-gray10/20 bg-white p-6 shadow-formal transition hover:border-brand-red/60 hover:-translate-y-0.5"
          >
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-brand-red">{item.eyebrow}</p>
              <h3 className="mt-3 font-display text-3xl">{item.title}</h3>
              <p className="mt-3 text-sm leading-6 text-brand-ink/65">{item.description}</p>
            </div>
            <span className="mt-6 text-sm font-semibold uppercase tracking-[0.12em] text-brand-red">Открыть раздел →</span>
          </Link>
        ))}
      </section>

      <section className="overflow-hidden rounded-3xl border border-brand-gray10/20 bg-white shadow-formal">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-brand-gray10/10 px-6 py-5">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-brand-red">Recent applications</p>
            <h3 className="mt-2 font-display text-3xl">Последние заявки</h3>
          </div>
          <Link to="/admin/candidates" className="text-sm font-semibold uppercase tracking-[0.12em] text-brand-red transition hover:text-brand-black">
            Все заявки →
          </Link>
        </div>

        {error ? (
          <div className="space-y-4 px-6 py-6">
            <p className="rounded-2xl border border-brand-red/20 bg-brand-red/10 px-4 py-3 text-sm leading-6 text-brand-ink">{error}</p>
            {retryable ? (
              <button
                type="button"
                className="border border-brand-red px-5 py-2 text-sm font-semibold uppercase tracking-[0.1em] text-brand-red transition hover:bg-brand-red hover:text-white"
                onClick={() => setRetryIndex((value) => value + 1)}
              >
                Повторить
              </button>
            ) : null}
          </div>
        ) : loading ? (
          <p className="px-6 py-10 text-sm text-brand-ink/60">Загрузка последних заявок...</p>
        ) : items.length === 0 ? (
          <p className="px-6 py-10 text-sm text-brand-ink/60">Заявок пока нет.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-brand-gray10/10">
              <thead className="bg-brand-paperAlt text-left text-xs uppercase tracking-[0.12em] text-brand-ink/60">
                <tr>
                  <th className="px-6 py-4 font-semibold">Кандидат</th>
                  <th className="px-6 py-4 font-semibold">Статус</th>
                  <th className="px-6 py-4 font-semibold">Получено</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-gray10/10">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-brand-paper/60">
                    <td className="px-6 py-5">
                      <Link to={`/admin/candidates/${item.id}`} className="font-semibold text-brand-black transition hover:text-brand-red">
                        {item.full_name ?? `Кандидат #${item.id}`}
                      </Link>
                      <p className="mt-1 text-xs uppercase tracking-[0.14em] text-brand-ink/50">ID {item.id}</p>
                    </td>
                    <td className="px-6 py-5">
                      <AdminStatusPill status={item.status} />
                    </td>
                    <td className="px-6 py-5 text-sm text-brand-ink/70">{DATE_FORMAT.format(new Date(item.created_at))}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
