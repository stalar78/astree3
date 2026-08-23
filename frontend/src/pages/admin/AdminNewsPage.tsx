import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { AdminApiError } from '../../admin/adminApi';
import { AdminPublicationStatus, AdminContentEmpty, AdminLoadingState, AdminNotice } from '../../admin/AdminContentPrimitives';
import { formatContentLoadError } from '../../admin/adminContentMessages';
import { ADMIN_CONTENT_PAGE_SIZE, listAdminNews, listAdminVideos, type AdminNewsListItem, type AdminVideoListItem, type PublishedFilter } from '../../admin/adminContentApi';

const DATE = new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' });

export function AdminNewsPage() {
  return <ContentListPage entity="news" />;
}

export function AdminVideosPage() {
  return <ContentListPage entity="video" />;
}

function ContentListPage({ entity }: { entity: 'news' | 'video' }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [items, setItems] = useState<Array<AdminNewsListItem | AdminVideoListItem>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);
  const [retryIndex, setRetryIndex] = useState(0);

  const published = normalizePublished(searchParams.get('published'));
  const offset = normalizeOffset(searchParams.get('offset'));

  useEffect(() => {
    document.title = `${entity === 'news' ? 'Новости' : 'Видео'} | Astrea Admin`;
  }, [entity]);

  useEffect(() => {
    const canonical = new URLSearchParams();
    if (published) canonical.set('published', published);
    if (offset > 0) canonical.set('offset', String(offset));
    if (searchParams.toString() !== canonical.toString()) {
      setSearchParams(canonical, { replace: true });
    }
  }, [offset, published, searchParams, setSearchParams]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setErrorStatus(null);

    const loader = entity === 'news' ? listAdminNews({ published, offset }, controller.signal) : listAdminVideos({ published, offset }, controller.signal);
    void loader
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
  }, [entity, location.pathname, location.search, navigate, offset, published, retryIndex]);

  const setOperational = (nextPublished: PublishedFilter, nextOffset = 0) => {
    const next = new URLSearchParams();
    if (nextPublished) next.set('published', nextPublished);
    if (nextOffset) next.set('offset', String(nextOffset));
    setSearchParams(next);
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-brand-red">Admin content</p>
          <h2 className="mt-3 font-display text-5xl">{entity === 'news' ? 'Новости' : 'Видео'}</h2>
        </div>
        <Link to={entity === 'news' ? '/admin/news/new' : '/admin/videos/new'} className="border border-brand-red bg-brand-red px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] text-white transition hover:bg-transparent hover:text-brand-red">
          Добавить
        </Link>
      </div>
      <div className="flex flex-wrap gap-3" aria-label="Фильтр публикации">
        {([
          ['', 'Все'],
          ['true', 'Опубликованные'],
          ['false', 'Черновики'],
        ] as const).map(([value, label]) => (
          <button
            key={value}
            type="button"
            onClick={() => setOperational(value)}
            className={`border px-4 py-2 text-sm uppercase tracking-[0.1em] transition ${published === value ? 'border-brand-red bg-brand-red text-white' : 'border-brand-gray10/25 bg-white text-brand-ink hover:border-brand-red'}`}
          >
            {label}
          </button>
        ))}
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
        <div className="flex flex-wrap justify-between gap-3 border-b border-brand-gray10/15 px-5 py-4 text-sm uppercase tracking-[0.12em] text-brand-ink/60">
          <span>{loading ? 'Загрузка...' : `${items.length} материалов на странице`}</span>
          <div className="flex gap-2">
            <button type="button" disabled={!offset || loading} onClick={() => setOperational(published, Math.max(0, offset - ADMIN_CONTENT_PAGE_SIZE))} className="border border-brand-gray10/25 px-4 py-2 disabled:opacity-40">
              Назад
            </button>
            <button type="button" disabled={items.length !== ADMIN_CONTENT_PAGE_SIZE || loading} onClick={() => setOperational(published, offset + ADMIN_CONTENT_PAGE_SIZE)} className="border border-brand-gray10/25 px-4 py-2 disabled:opacity-40">
              Далее
            </button>
          </div>
        </div>
        {loading ? (
          <div className="p-5">
            <AdminLoadingState />
          </div>
        ) : error ? null : items.length === 0 ? (
          <AdminContentEmpty>Материалов пока нет.</AdminContentEmpty>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-brand-gray10/10">
              <thead className="bg-brand-paperAlt text-left text-xs uppercase tracking-[0.12em] text-brand-ink/60">
                <tr>
                  <th className="px-5 py-4">Название</th>
                  <th className="px-5 py-4">Статус</th>
                  <th className="px-5 py-4">Опубликовано</th>
                  <th className="px-5 py-4">Обновлено</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-gray10/10">
                {items.map((item) => (
                  <tr key={item.id} className="align-top hover:bg-brand-paper/60">
                    <td className="px-5 py-5">
                      <Link to={`/admin/${entity === 'news' ? 'news' : 'videos'}/${item.id}`} className="font-semibold hover:text-brand-red">
                        {item.title}
                      </Link>
                      <p className="mt-1 text-xs text-brand-ink/55">{entity === 'news' ? (item as AdminNewsListItem).slug : (item as AdminVideoListItem).source_url}</p>
                    </td>
                    <td className="px-5 py-5"><AdminPublicationStatus published={item.is_published} /></td>
                    <td className="px-5 py-5 text-sm text-brand-ink/70">{item.published_at ? DATE.format(new Date(item.published_at)) : '—'}</td>
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

function normalizePublished(value: string | null): PublishedFilter {
  return value === 'true' || value === 'false' ? value : '';
}

function normalizeOffset(value: string | null): number {
  if (!value || !/^\d+$/.test(value)) return 0;
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed >= 0 ? parsed : 0;
}
