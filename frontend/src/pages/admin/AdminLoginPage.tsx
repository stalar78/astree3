import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AdminApiError, loginAdmin } from '../../admin/adminApi';
import { formatAdminError } from '../../admin/adminMessages';
import { useAdminSession } from '../../admin/useAdminSession';

type LoginState = { from?: string } | null;

export function AdminLoginPage() {
  const session = useAdminSession();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as LoginState)?.from ?? '/admin/candidates';

  useEffect(() => {
    document.title = 'Вход администратора | Astrea';
  }, []);

  useEffect(() => {
    if (session.status === 'authenticated') {
      navigate(from, { replace: true });
    }
  }, [from, navigate, session.status]);

  if (session.status === 'loading') {
    return <CenteredLoginState title="Проверка сессии" message="Пожалуйста, подождите." />;
  }

  if (session.status === 'authenticated') {
    return <CenteredLoginState title="Открываем кабинет" message="Перенаправление..." />;
  }

  return (
    <div className="grid min-h-screen bg-[radial-gradient(circle_at_top,rgba(218,41,28,0.08),transparent_28%),linear-gradient(180deg,#f4f0e8_0%,#efe8dc_100%)] px-6 py-12 text-brand-ink">
      <div className="mx-auto flex w-full max-w-md flex-col justify-center">
        <div className="rounded-3xl border border-brand-gray10/20 bg-white/95 p-8 shadow-formal">
          <p className="text-xs uppercase tracking-[0.24em] text-brand-red">Admin login</p>
          <h1 className="mt-4 font-display text-4xl">Вход</h1>
          <p className="mt-3 text-sm leading-6 text-brand-ink/70">Доступ только по серверной сессии.</p>
          {session.status === 'error' ? (
            <Notice className="mt-6">{session.message}</Notice>
          ) : null}
          {error ? <Notice className="mt-4">{error}</Notice> : null}
          <form
            className="mt-8 grid gap-5"
            onSubmit={async (event) => {
              event.preventDefault();
              setSubmitting(true);
              setError(null);
              try {
                await loginAdmin(username.trim(), password);
                navigate(from, { replace: true });
              } catch (caughtError) {
                const message =
                  caughtError instanceof AdminApiError && caughtError.status === 401
                    ? formatAdminError(caughtError, 'login')
                    : formatAdminError(caughtError, 'login');
                setError(message);
              } finally {
                setSubmitting(false);
              }
            }}
          >
            <label className="grid gap-2 text-sm font-semibold uppercase tracking-[0.12em]">
              Имя пользователя
              <input
                className="rounded-2xl border border-brand-gray10/20 bg-brand-paper px-4 py-3 text-base outline-none transition focus:border-brand-red"
                autoComplete="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                disabled={submitting}
              />
            </label>
            <label className="grid gap-2 text-sm font-semibold uppercase tracking-[0.12em]">
              Пароль
              <input
                className="rounded-2xl border border-brand-gray10/20 bg-brand-paper px-4 py-3 text-base outline-none transition focus:border-brand-red"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={submitting}
              />
            </label>
            <button
              type="submit"
              className="mt-2 inline-flex items-center justify-center rounded-full border border-brand-red bg-brand-red px-6 py-3 text-sm font-semibold uppercase tracking-[0.14em] text-white transition hover:bg-transparent hover:text-brand-red disabled:cursor-not-allowed disabled:opacity-60"
              disabled={submitting}
            >
              {submitting ? 'Вход...' : 'Войти'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function Notice({ children, className = '' }: { children: string; className?: string }) {
  return <p className={`rounded-2xl border border-brand-red/20 bg-brand-red/10 px-4 py-3 text-sm leading-6 text-brand-ink ${className}`}>{children}</p>;
}

function CenteredLoginState({ title, message }: { title: string; message: string }) {
  return (
    <div className="grid min-h-screen place-items-center bg-brand-paper px-6 text-center text-brand-ink">
      <div className="max-w-lg rounded-3xl border border-brand-gray10/20 bg-white px-8 py-10 shadow-formal">
        <p className="text-xs uppercase tracking-[0.24em] text-brand-red">Admin</p>
        <h1 className="mt-4 font-display text-4xl">{title}</h1>
        <p className="mt-4 text-base leading-7 text-brand-ink/75">{message}</p>
      </div>
    </div>
  );
}
