import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  AdminApiError,
  ADMIN_CANDIDATE_STATUSES,
  getAdminCandidate,
  getAdminCandidatePhoto,
  type AdminCandidateDetail,
  type AdminCandidateStatus,
  updateAdminCandidateStatus,
} from '../../admin/adminApi';
import { formatAdminError } from '../../admin/adminMessages';
import { AdminStatusPill } from '../../admin/AdminStatusPill';
import { ADMIN_CANDIDATE_STATUS_LABELS } from '../../admin/adminStatus';

const DATE_TIME_FORMAT = new Intl.DateTimeFormat('ru-RU', {
  dateStyle: 'medium',
  timeStyle: 'short',
});
const DATE_FORMAT = new Intl.DateTimeFormat('ru-RU', {
  dateStyle: 'medium',
});

export function AdminCandidateDetailPage() {
  const { candidateId } = useParams();
  const navigate = useNavigate();
  const numericId = Number(candidateId);
  const idIsValid = Number.isInteger(numericId) && numericId > 0;
  const [candidate, setCandidate] = useState<AdminCandidateDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const [photoLoading, setPhotoLoading] = useState(false);
  const [draftStatus, setDraftStatus] = useState<AdminCandidateStatus | ''>('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    document.title = 'Карточка кандидата | Astrea Admin';
  }, []);

  useEffect(() => {
    if (!idIsValid) {
      setLoading(false);
      setError('Запрос не прошёл проверку.');
      return;
    }

    const controller = new AbortController();
    let active = true;
    setLoading(true);
    setError(null);
    setCandidate(null);
    setPhotoUrl(null);
    setPhotoError(null);
    setDraftStatus('');
    setSaveError(null);

    void getAdminCandidate(numericId, controller.signal)
      .then((response) => {
        if (active) {
          setCandidate(response);
          setDraftStatus(response.status);
        }
      })
      .catch((caughtError: unknown) => {
        if (!active || controller.signal.aborted) {
          return;
        }
        if (caughtError instanceof AdminApiError && (caughtError.status === 401 || caughtError.status === 403)) {
          navigate('/admin/login', { replace: true, state: { from: `/admin/candidates/${numericId}` } });
          return;
        }
        setError(formatAdminError(caughtError, 'detail'));
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
  }, [idIsValid, navigate, numericId]);

  useEffect(() => {
    if (!candidate?.has_photo) {
      setPhotoUrl(null);
      setPhotoLoading(false);
      setPhotoError(null);
      return;
    }

    const controller = new AbortController();
    let currentUrl: string | null = null;
    setPhotoLoading(true);
    setPhotoError(null);
    setPhotoUrl(null);

    void getAdminCandidatePhoto(candidate.id, controller.signal)
      .then((blob) => {
        currentUrl = URL.createObjectURL(blob);
        setPhotoUrl(currentUrl);
      })
      .catch((caughtError: unknown) => {
        if (controller.signal.aborted) {
          return;
        }
        if (caughtError instanceof AdminApiError && (caughtError.status === 401 || caughtError.status === 403)) {
          navigate('/admin/login', { replace: true, state: { from: `/admin/candidates/${candidate.id}` } });
          return;
        }
        setPhotoError(formatAdminError(caughtError, 'photo'));
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setPhotoLoading(false);
        }
      });

    return () => {
      controller.abort();
      if (currentUrl) {
        URL.revokeObjectURL(currentUrl);
      }
    };
  }, [candidate?.has_photo, candidate?.id, navigate]);

  if (loading) {
    return <CenteredDetailState title="Загрузка кандидата" message="Пожалуйста, подождите." />;
  }

  if (error) {
    return <CenteredDetailState title="Карточка недоступна" message={error} />;
  }

  if (!candidate) {
    return <CenteredDetailState title="Кандидат не найден" message="Запись отсутствует." />;
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <Link to="/admin/candidates" className="text-sm font-semibold uppercase tracking-[0.14em] text-brand-ink/60 transition hover:text-brand-red">
            ← К списку
          </Link>
          <h2 className="mt-3 font-display text-5xl">{candidate.full_name ?? `Кандидат #${candidate.id}`}</h2>
          <p className="mt-3 text-sm uppercase tracking-[0.14em] text-brand-ink/60">ID {candidate.id}</p>
        </div>
        <AdminStatusPill status={candidate.status} />
      </div>

      {saveError ? <Notice>{saveError}</Notice> : null}

      <div className="grid gap-8 xl:grid-cols-[1.4fr_0.9fr]">
        <section className="space-y-8">
          <Card title="Сведения">
            <DetailGrid
              items={[
                ['ФИО', candidate.full_name],
                ['Дата рождения', candidate.date_of_birth ? DATE_FORMAT.format(new Date(candidate.date_of_birth)) : null],
                ['Город', candidate.city],
                ['Телефон', candidate.phone],
                ['Email', candidate.email],
                ['Образование', candidate.education],
                ['Работа', candidate.occupation],
                ['Семейное положение', candidate.marital_status],
                ['Организации', candidate.other_organizations],
                ['Соцсети', candidate.social_links],
                ['Создано', DATE_TIME_FORMAT.format(new Date(candidate.created_at))],
                ['Обновлено', DATE_TIME_FORMAT.format(new Date(candidate.updated_at))],
              ]}
            />
          </Card>

          <Card title="Мотивация">
            <p className="whitespace-pre-wrap text-sm leading-7 text-brand-ink/80">{candidate.motivation ?? '—'}</p>
          </Card>

          <Card title="Согласия">
            <div className="grid gap-4">
              {candidate.consents.map((consent) => (
                <div key={`${consent.consent_type}-${consent.document_version}`} className="rounded-2xl border border-brand-gray10/15 bg-brand-paper px-4 py-4">
                  <p className="text-sm font-semibold uppercase tracking-[0.12em] text-brand-ink">{consent.consent_type}</p>
                  <p className="mt-2 text-sm text-brand-ink/75">Версия: {consent.document_version}</p>
                  <p className="mt-1 text-sm text-brand-ink/75">Принято: {DATE_TIME_FORMAT.format(new Date(consent.accepted_at))}</p>
                </div>
              ))}
            </div>
          </Card>
        </section>

        <aside className="space-y-8">
          <Card title="Фотография">
            {candidate.has_photo ? (
              <>
                {photoLoading ? <p className="text-sm text-brand-ink/70">Загрузка фотографии...</p> : null}
                {photoError ? <Notice>{photoError}</Notice> : null}
                {photoUrl ? <img className="mt-4 w-full rounded-2xl border border-brand-gray10/15 object-cover" src={photoUrl} alt={candidate.full_name ?? `Кандидат #${candidate.id}`} /> : null}
              </>
            ) : (
              <p className="text-sm text-brand-ink/70">Фотография отсутствует.</p>
            )}
          </Card>

          <Card title="Статус">
            <div className="grid gap-4">
              <label className="grid gap-2 text-sm font-semibold uppercase tracking-[0.12em]">
                Текущий статус
                <select
                  className="rounded-2xl border border-brand-gray10/20 bg-brand-paper px-4 py-3 text-base outline-none transition focus:border-brand-red"
                  value={draftStatus}
                  onChange={(event) => setDraftStatus(event.target.value as AdminCandidateStatus)}
                >
                  {ADMIN_CANDIDATE_STATUSES.map((status) => (
                    <option key={status} value={status}>
                      {ADMIN_CANDIDATE_STATUS_LABELS[status]}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                className="inline-flex items-center justify-center rounded-full border border-brand-red bg-brand-red px-6 py-3 text-sm font-semibold uppercase tracking-[0.14em] text-white transition hover:bg-transparent hover:text-brand-red disabled:cursor-not-allowed disabled:opacity-60"
                disabled={saving || draftStatus === candidate.status}
                onClick={async () => {
                  if (!draftStatus || draftStatus === candidate.status) {
                    return;
                  }
                  setSaving(true);
                  setSaveError(null);
                  try {
                    const response = await updateAdminCandidateStatus(candidate.id, draftStatus);
                    setCandidate((current) => (current ? { ...current, status: response.status } : current));
                  } catch (caughtError) {
                    if (caughtError instanceof AdminApiError && (caughtError.status === 401 || caughtError.status === 403)) {
                      navigate('/admin/login', { replace: true, state: { from: `/admin/candidates/${candidate.id}` } });
                      return;
                    }
                    setSaveError(formatAdminError(caughtError, 'update'));
                  } finally {
                    setSaving(false);
                  }
                }}
              >
                {saving ? 'Сохранение...' : 'Сохранить'}
              </button>
            </div>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-3xl border border-brand-gray10/20 bg-white p-6 shadow-formal">
      <h3 className="font-display text-3xl">{title}</h3>
      <div className="mt-5">{children}</div>
    </section>
  );
}

function DetailGrid({ items }: { items: Array<[string, string | null]> }) {
  return (
    <dl className="grid gap-4 md:grid-cols-2">
      {items.map(([label, value]) => (
        <div key={label} className="rounded-2xl border border-brand-gray10/15 bg-brand-paper px-4 py-4">
          <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-brand-ink/55">{label}</dt>
          <dd className="mt-2 text-sm leading-6 text-brand-ink/85">{value ?? '—'}</dd>
        </div>
      ))}
    </dl>
  );
}

function Notice({ children }: { children: string }) {
  return <p className="rounded-2xl border border-brand-red/20 bg-brand-red/10 px-4 py-3 text-sm leading-6 text-brand-ink">{children}</p>;
}

function CenteredDetailState({ title, message }: { title: string; message: string }) {
  return (
    <div className="grid min-h-[60vh] place-items-center rounded-3xl border border-brand-gray10/20 bg-white px-8 py-10 shadow-formal">
      <div className="max-w-lg text-center">
        <p className="text-xs uppercase tracking-[0.24em] text-brand-red">Admin</p>
        <h1 className="mt-4 font-display text-4xl">{title}</h1>
        <p className="mt-4 text-base leading-7 text-brand-ink/75">{message}</p>
      </div>
    </div>
  );
}
