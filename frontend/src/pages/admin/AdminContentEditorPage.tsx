import { useEffect, useState, type FormEvent, type ReactNode } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { AdminApiError } from '../../admin/adminApi';
import {
  createAdminNews,
  createAdminVideo,
  deleteAdminNews,
  deleteAdminVideo,
  getAdminNews,
  getAdminPage,
  getAdminVideo,
  updateAdminNews,
  updateAdminPage,
  updateAdminVideo,
  type AdminNewsDetail,
  type AdminPageDetail,
  type AdminVideoDetail,
  type NewsPayload,
  type PagePayload,
  type VideoPayload,
} from '../../admin/adminContentApi';
import { AdminBackLink, AdminDeleteControl, AdminField, AdminInput, AdminLoadingState, AdminMeta, AdminNotice, AdminSaveButton, AdminTextarea } from '../../admin/AdminContentPrimitives';
import { formatContentLoadError, formatContentMutationError } from '../../admin/adminContentMessages';

const DATE = new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' });

export function AdminNewsEditorPage({ create = false }: { create?: boolean }) {
  const { newsId } = useParams();
  const id = Number(newsId);
  return <NewsEditor create={create} id={Number.isInteger(id) && id > 0 ? id : null} />;
}

export function AdminVideoEditorPage({ create = false }: { create?: boolean }) {
  const { videoId } = useParams();
  const id = Number(videoId);
  return <VideoEditor create={create} id={Number.isInteger(id) && id > 0 ? id : null} />;
}

export function AdminPageEditorPage() {
  const { pageKey } = useParams();
  return <PageEditor pageKey={pageKey ?? ''} />;
}

function NewsEditor({ create, id }: { create: boolean; id: number | null }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState<NewsPayload>(emptyNews());
  const [baseline, setBaseline] = useState<NewsPayload>(emptyNews());
  const [item, setItem] = useState<AdminNewsDetail | null>(null);
  const [loading, setLoading] = useState(!create);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadErrorStatus, setLoadErrorStatus] = useState<number | null>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [deleteArmed, setDeleteArmed] = useState(false);
  const [loadRetryIndex, setLoadRetryIndex] = useState(0);

  useEffect(() => {
    document.title = `${create ? 'Новая новость' : 'Редактирование новости'} | Astrea Admin`;
  }, [create]);

  useEffect(() => {
    if (create) return;
    if (!id) {
      setLoading(false);
      setLoadError('Запрос не прошёл проверку.');
      setLoadErrorStatus(422);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setLoadError(null);
    setLoadErrorStatus(null);
    setMutationError(null);
    void getAdminNews(id, controller.signal)
      .then((value) => {
        const next = newsPayload(value);
        setItem(value);
        setForm(next);
        setBaseline(next);
      })
      .catch((caughtError: unknown) => {
        if (controller.signal.aborted) return;
        if (caughtError instanceof AdminApiError && caughtError.status === 401) {
          navigate('/admin/login', { replace: true, state: { from: `${location.pathname}${location.search}` } });
          return;
        }
        setLoadError(formatContentLoadError(caughtError, 'detail'));
        setLoadErrorStatus(caughtError instanceof AdminApiError ? caughtError.status : null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [create, id, loadRetryIndex, location.pathname, location.search, navigate]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMutationError(null);
    setSaved(false);
    try {
      const response = create ? await createAdminNews(form) : await updateAdminNews(id!, changed(form, baseline));
      const next = newsPayload(response);
      setItem(response);
      setForm(next);
      setBaseline(next);
      setSaved(true);
      if (create) navigate(`/admin/news/${response.id}`, { replace: true });
    } catch (caughtError: unknown) {
      if (caughtError instanceof AdminApiError && caughtError.status === 401) {
        navigate('/admin/login', { replace: true, state: { from: `${location.pathname}${location.search}` } });
        return;
      }
      setMutationError(formatContentMutationError(caughtError, 'news', create ? 'create' : 'update'));
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!id) return;
    setBusy(true);
    setMutationError(null);
    try {
      await deleteAdminNews(id);
      navigate('/admin/news', { replace: true });
    } catch (caughtError: unknown) {
      if (caughtError instanceof AdminApiError && caughtError.status === 401) {
        navigate('/admin/login', { replace: true, state: { from: `${location.pathname}${location.search}` } });
        return;
      }
      setMutationError(formatContentMutationError(caughtError, 'news', 'delete'));
      setDeleteArmed(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <EditorLayout
      title={create ? 'Новая новость' : 'Редактирование новости'}
      backTo="/admin/news"
      loading={loading}
      loadError={loadError}
      loadErrorStatus={loadErrorStatus}
      onRetry={create ? undefined : () => setLoadRetryIndex((value) => value + 1)}
      mutationError={mutationError}
    >
      <form onSubmit={save} className="space-y-7">
        <AdminField label="Заголовок" required>
          <AdminInput required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
        </AdminField>
        <AdminField label="Slug" required help="Строчные латинские буквы, цифры и дефисы.">
          <AdminInput required value={form.slug} onChange={(event) => setForm({ ...form, slug: event.target.value })} />
        </AdminField>
        <AdminField label="Анонс" required>
          <AdminTextarea required value={form.excerpt} onChange={(event) => setForm({ ...form, excerpt: event.target.value })} />
        </AdminField>
        <AdminField label="Текст" required>
          <AdminTextarea required className="min-h-[22rem]" value={form.body} onChange={(event) => setForm({ ...form, body: event.target.value })} />
        </AdminField>
        <AdminField label="URL изображения" help="HTTPS-ссылка или путь сайта, начинающийся с /.">
          <AdminInput type="text" inputMode="url" value={form.image_url ?? ''} onChange={(event) => setForm({ ...form, image_url: event.target.value || null })} />
        </AdminField>
        <PublicationToggle value={form.is_published} onChange={(value) => setForm({ ...form, is_published: value })} />
        <EditorActions busy={busy} saved={saved} dirty={create || JSON.stringify(form) !== JSON.stringify(baseline)} />
      </form>
      {!create && id ? (
        <div className="pt-6">
          <AdminDeleteControl armed={deleteArmed} busy={busy} onArm={() => setDeleteArmed(true)} onCancel={() => setDeleteArmed(false)} onConfirm={remove} />
        </div>
      ) : null}
      {item ? <AdminMeta items={meta(item)} /> : null}
    </EditorLayout>
  );
}

function VideoEditor({ create, id }: { create: boolean; id: number | null }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState<VideoPayload>(emptyVideo());
  const [baseline, setBaseline] = useState<VideoPayload>(emptyVideo());
  const [item, setItem] = useState<AdminVideoDetail | null>(null);
  const [loading, setLoading] = useState(!create);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadErrorStatus, setLoadErrorStatus] = useState<number | null>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [deleteArmed, setDeleteArmed] = useState(false);
  const [loadRetryIndex, setLoadRetryIndex] = useState(0);

  useEffect(() => {
    document.title = `${create ? 'Новое видео' : 'Редактирование видео'} | Astrea Admin`;
  }, [create]);

  useEffect(() => {
    if (create) return;
    if (!id) {
      setLoading(false);
      setLoadError('Запрос не прошёл проверку.');
      setLoadErrorStatus(422);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setLoadError(null);
    setLoadErrorStatus(null);
    setMutationError(null);
    void getAdminVideo(id, controller.signal)
      .then((value) => {
        const next = videoPayload(value);
        setItem(value);
        setForm(next);
        setBaseline(next);
      })
      .catch((caughtError: unknown) => {
        if (controller.signal.aborted) return;
        if (caughtError instanceof AdminApiError && caughtError.status === 401) {
          navigate('/admin/login', { replace: true, state: { from: `${location.pathname}${location.search}` } });
          return;
        }
        setLoadError(formatContentLoadError(caughtError, 'detail'));
        setLoadErrorStatus(caughtError instanceof AdminApiError ? caughtError.status : null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [create, id, loadRetryIndex, location.pathname, location.search, navigate]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMutationError(null);
    setSaved(false);
    try {
      const response = create ? await createAdminVideo(form) : await updateAdminVideo(id!, changed(form, baseline));
      const next = videoPayload(response);
      setItem(response);
      setForm(next);
      setBaseline(next);
      setSaved(true);
      if (create) navigate(`/admin/videos/${response.id}`, { replace: true });
    } catch (caughtError: unknown) {
      if (caughtError instanceof AdminApiError && caughtError.status === 401) {
        navigate('/admin/login', { replace: true, state: { from: `${location.pathname}${location.search}` } });
        return;
      }
      setMutationError(formatContentMutationError(caughtError, 'video', create ? 'create' : 'update'));
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!id) return;
    setBusy(true);
    setMutationError(null);
    try {
      await deleteAdminVideo(id);
      navigate('/admin/videos', { replace: true });
    } catch (caughtError: unknown) {
      if (caughtError instanceof AdminApiError && caughtError.status === 401) {
        navigate('/admin/login', { replace: true, state: { from: `${location.pathname}${location.search}` } });
        return;
      }
      setMutationError(formatContentMutationError(caughtError, 'video', 'delete'));
      setDeleteArmed(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <EditorLayout
      title={create ? 'Новое видео' : 'Редактирование видео'}
      backTo="/admin/videos"
      loading={loading}
      loadError={loadError}
      loadErrorStatus={loadErrorStatus}
      onRetry={create ? undefined : () => setLoadRetryIndex((value) => value + 1)}
      mutationError={mutationError}
    >
      <form onSubmit={save} className="space-y-7">
        <AdminField label="Заголовок" required>
          <AdminInput required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
        </AdminField>
        <AdminField label="Описание" required>
          <AdminTextarea required value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
        </AdminField>
        <AdminField label="Ссылка RuTube" required help="Используйте ссылку на видео RuTube.">
          <AdminInput required type="url" value={form.source_url} onChange={(event) => setForm({ ...form, source_url: event.target.value })} />
        </AdminField>
        <PublicationToggle value={form.is_published} onChange={(value) => setForm({ ...form, is_published: value })} />
        <EditorActions busy={busy} saved={saved} dirty={create || JSON.stringify(form) !== JSON.stringify(baseline)} />
      </form>
      {!create && id ? (
        <div className="pt-6">
          <AdminDeleteControl armed={deleteArmed} busy={busy} onArm={() => setDeleteArmed(true)} onCancel={() => setDeleteArmed(false)} onConfirm={remove} />
        </div>
      ) : null}
      {item ? <AdminMeta items={meta(item)} /> : null}
    </EditorLayout>
  );
}

function PageEditor({ pageKey }: { pageKey: string }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState<PagePayload>({ title: '', content: '', is_published: false });
  const [baseline, setBaseline] = useState<PagePayload>(form);
  const [item, setItem] = useState<AdminPageDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadErrorStatus, setLoadErrorStatus] = useState<number | null>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loadRetryIndex, setLoadRetryIndex] = useState(0);

  useEffect(() => {
    document.title = 'Редактирование страницы | Astrea Admin';
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setLoadError(null);
    setLoadErrorStatus(null);
    setMutationError(null);
    void getAdminPage(pageKey, controller.signal)
      .then((value) => {
        const next = { title: value.title, content: value.content, is_published: value.is_published };
        setItem(value);
        setForm(next);
        setBaseline(next);
      })
      .catch((caughtError: unknown) => {
        if (controller.signal.aborted) return;
        if (caughtError instanceof AdminApiError && caughtError.status === 401) {
          navigate('/admin/login', { replace: true, state: { from: `${location.pathname}${location.search}` } });
          return;
        }
        setLoadError(formatContentLoadError(caughtError, 'detail'));
        setLoadErrorStatus(caughtError instanceof AdminApiError ? caughtError.status : null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [loadRetryIndex, location.pathname, location.search, navigate, pageKey]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMutationError(null);
    setSaved(false);
    try {
      const response = await updateAdminPage(pageKey, changed(form, baseline));
      const next = { title: response.title, content: response.content, is_published: response.is_published };
      setItem(response);
      setForm(next);
      setBaseline(next);
      setSaved(true);
    } catch (caughtError: unknown) {
      if (caughtError instanceof AdminApiError && caughtError.status === 401) {
        navigate('/admin/login', { replace: true, state: { from: `${location.pathname}${location.search}` } });
        return;
      }
      setMutationError(formatContentMutationError(caughtError, 'page', 'update'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <EditorLayout
      title="Редактирование страницы"
      backTo="/admin/pages"
      loading={loading}
      loadError={loadError}
      loadErrorStatus={loadErrorStatus}
      onRetry={() => setLoadRetryIndex((value) => value + 1)}
      mutationError={mutationError}
    >
      <div className="mb-6 border border-brand-gray10/20 bg-brand-paper px-4 py-3 text-sm">
        Ключ страницы: <code>{pageKey}</code>
      </div>
      <form onSubmit={save} className="space-y-7">
        <AdminField label="Заголовок" required>
          <AdminInput required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
        </AdminField>
        <AdminField label="Содержание" required>
          <AdminTextarea required className="min-h-[28rem]" value={form.content} onChange={(event) => setForm({ ...form, content: event.target.value })} />
        </AdminField>
        <PublicationToggle value={form.is_published} onChange={(value) => setForm({ ...form, is_published: value })} />
        <EditorActions busy={busy} saved={saved} dirty={JSON.stringify(form) !== JSON.stringify(baseline)} />
      </form>
      {item ? <AdminMeta items={meta(item)} /> : null}
    </EditorLayout>
  );
}

function EditorLayout({
  title,
  backTo,
  loading,
  loadError,
  loadErrorStatus,
  onRetry,
  mutationError,
  children,
}: {
  title: string;
  backTo: string;
  loading: boolean;
  loadError: string | null;
  loadErrorStatus: number | null;
  onRetry?: () => void;
  mutationError: string | null;
  children: ReactNode;
}) {
  const showEditor = !loading && !loadError;
  return (
    <div className="space-y-7">
      <AdminBackLink to={backTo}>К списку</AdminBackLink>
      <h2 className="font-display text-5xl">{title}</h2>
      {loading ? <AdminLoadingState /> : null}
      {!loading && loadError ? (
        <div className="space-y-3">
          <AdminNotice>{loadError}</AdminNotice>
          {onRetry && (loadErrorStatus === null || loadErrorStatus === 503) ? (
            <button type="button" onClick={onRetry} className="border border-brand-red px-5 py-2 text-sm font-semibold uppercase tracking-[0.1em] text-brand-red">
              Повторить
            </button>
          ) : null}
        </div>
      ) : null}
      {showEditor ? (
        <section className="border border-brand-gray10/20 bg-white p-5 shadow-formal sm:p-8">
          {mutationError ? <div className="mb-6"><AdminNotice>{mutationError}</AdminNotice></div> : null}
          {children}
        </section>
      ) : null}
    </div>
  );
}

function PublicationToggle({ value, onChange }: { value: boolean; onChange: (value: boolean) => void }) {
  return (
    <label className="flex items-center gap-3 text-sm font-semibold">
      <input type="checkbox" checked={value} onChange={(event) => onChange(event.target.checked)} className="h-5 w-5 accent-brand-red" />
      Опубликовано
    </label>
  );
}

function EditorActions({ busy, saved, dirty }: { busy: boolean; saved: boolean; dirty: boolean }) {
  return (
    <div className="flex flex-wrap items-center gap-4 border-t border-brand-gray10/15 pt-6">
      <AdminSaveButton busy={busy} />
      {saved ? <span className="text-sm text-brand-red" role="status">Сохранено.</span> : dirty ? <span className="text-sm text-brand-ink/60">Есть несохранённые изменения.</span> : null}
    </div>
  );
}

function emptyNews(): NewsPayload {
  return { slug: '', title: '', excerpt: '', body: '', image_url: null, is_published: false };
}

function emptyVideo(): VideoPayload {
  return { title: '', description: '', source_url: '', is_published: false };
}

function newsPayload(value: AdminNewsDetail): NewsPayload {
  return { slug: value.slug, title: value.title, excerpt: value.excerpt, body: value.body, image_url: value.image_url, is_published: value.is_published };
}

function videoPayload(value: AdminVideoDetail): VideoPayload {
  return { title: value.title, description: value.description, source_url: value.source_url, is_published: value.is_published };
}

function changed<T extends Record<string, unknown>>(value: T, baseline: T): Partial<T> {
  const patch: Partial<T> = {};
  for (const [key, nextValue] of Object.entries(value)) {
    if (JSON.stringify(nextValue) !== JSON.stringify(baseline[key])) {
      patch[key as keyof T] = nextValue as T[keyof T];
    }
  }
  return patch;
}

function meta(value: AdminNewsDetail | AdminVideoDetail | AdminPageDetail): Array<[string, string | null]> {
  return [
    ['Создано', 'created_at' in value ? DATE.format(new Date(value.created_at)) : null],
    ['Обновлено', DATE.format(new Date(value.updated_at))],
    ['Опубликовано', 'published_at' in value && value.published_at ? DATE.format(new Date(value.published_at)) : null],
  ];
}
