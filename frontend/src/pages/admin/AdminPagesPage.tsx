import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AdminApiError } from '../../admin/adminApi';
import { listAdminPages, type AdminPageListItem } from '../../admin/adminContentApi';
import { AdminContentEmpty, AdminLoadingState, AdminNotice, AdminPublicationStatus } from '../../admin/AdminContentPrimitives';
import { formatContentLoadError } from '../../admin/adminContentMessages';

const DATE = new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' });

export function AdminPagesPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [items, setItems] = useState<AdminPageListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);
  const [retryIndex, setRetryIndex] = useState(0);

  useEffect(() => {
    document.title = 'Страницы | Astrea Admin';
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setErrorStatus(null);

    void listAdminPages(controller.signal)
      .then((response) => {
        setItems(response.items);
      })
      .catch((caughtError: unknown) => {
        if (controller.signal.aborted) return;
        if (caughtError instanceof AdminApiError && caughtError.status === 401) {
          navigate('/admin/login', { replace: true, state: { from: `${location.pathname}${location.search}` } });
          return;
        }
        setItems([]);
        setErrorStatus(caughtError instanceof AdminApiError ? caughtError.status : null);
        setError(formatContentLoadError(caughtError, 'list'));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [location.pathname, location.search, navigate, retryIndex]);

  return (
    <div className="space-y-8">
      <div>
        <p className="text-xs uppercase tracking-[0.24em] text-brand-red">Admin content</p>
        <h2 className="mt-3 font-display text-5xl">Страницы</h2>
      </div>
      {error ? (
        <div className="space-y-3">
          <AdminNotice>{error}</AdminNotice>
          {(errorStatus === null || errorStatus === 503) ? (
            <button type="button" onClick={() => setRetryIndex((value) => value + 1)} className="border border-brand-red px-5 py-2 text-sm font-semibold uppercase tracking-[0.1em] text-brand-red">
              Повторить
            </button>
          ) : null}
        </div>
      ) : null}
      <section className="border border-brand-gray10/20 bg-white">
        <div className="border-b border-brand-gray10/15 px-5 py-4 text-sm uppercase tracking-[0.12em] text-brand-ink/60">
          {loading ? 'Загрузка...' : 'Существующие страницы'}
        </div>
        {loading ? (
          <div className="p-5"><AdminLoadingState /></div>
        ) : error ? null : items.length === 0 ? (
          <AdminContentEmpty>Страницы пока не заведены.</AdminContentEmpty>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-brand-gray10/10">
              <thead className="bg-brand-paperAlt text-left text-xs uppercase tracking-[0.12em] text-brand-ink/60">
                <tr>
                  <th className="px-5 py-4">Ключ</th>
                  <th className="px-5 py-4">Название</th>
                  <th className="px-5 py-4">Статус</th>
                  <th className="px-5 py-4">Обновлено</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-gray10/10">
                {items.map((item) => (
                  <tr key={item.key} className="align-top hover:bg-brand-paper/60">
                    <td className="px-5 py-5"><code>{item.key}</code></td>
                    <td className="px-5 py-5"><Link to={`/admin/pages/${item.key}`} className="font-semibold hover:text-brand-red">{item.title}</Link></td>
                    <td className="px-5 py-5"><AdminPublicationStatus published={item.is_published} /></td>
                    <td className="px-5 py-5 text-sm text-brand-ink/70">{DATE.format(new Date(item.updated_at))}</td>
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
