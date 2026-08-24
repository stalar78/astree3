import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { AdminApiError, logoutAdmin } from './adminApi';
import { SESSION_SECURITY_MESSAGE } from './adminMessages';
import { useAdminSession } from './useAdminSession';

export function AdminProtectedLayout() {
  const { state: session, retry } = useAdminSession();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (session.status === 'anonymous') {
      navigate('/admin/login', { replace: true, state: { from: `${location.pathname}${location.search}` } });
    }
  }, [location.pathname, location.search, navigate, session.status]);

  if (session.status === 'loading') {
    return <AdminCenteredState title="Проверка сессии" message="Пожалуйста, подождите." />;
  }

  if (session.status === 'error') {
    return <AdminCenteredState title="Админ-панель недоступна" message={session.message} actionLabel="Повторить" onAction={retry} />;
  }

  if (session.status !== 'authenticated') {
    return null;
  }

  return (
    <AdminShell
      username={session.username}
      onLogout={async () => {
        const result = await logoutAdminWithOutcome();
        if (result === 'signed_out' || result === 'session_missing') {
          navigate('/admin/login', { replace: true });
        }
        return result;
      }}
    >
      <Outlet />
    </AdminShell>
  );
}

export function AdminShell({
  username,
  onLogout,
  children,
}: {
  username: string;
  onLogout: () => Promise<LogoutOutcome>;
  children: ReactNode;
}) {
  const [logoutState, setLogoutState] = useState<string | null>(null);
  const [logoutBusy, setLogoutBusy] = useState(false);

  return (
    <div className="min-h-screen bg-brand-paper text-brand-ink">
      <header className="border-b border-brand-gray10/20 bg-brand-black text-white shadow-formal">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-5 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-brand-gray6">Admin console</p>
            <h1 className="font-display text-3xl">Панель управления</h1>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {[
              { to: '/admin', label: 'Обзор', end: true },
              { to: '/admin/candidates', label: 'Кандидаты', end: false },
              { to: '/admin/news', label: 'Новости', end: false },
              { to: '/admin/videos', label: 'Видео', end: false },
              { to: '/admin/pages', label: 'Страницы', end: false },
            ].map(({ to, label, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  `border px-4 py-2 text-sm uppercase tracking-[0.14em] transition ${
                    isActive ? 'border-brand-red bg-brand-red text-white' : 'border-white/15 text-white/90 hover:border-white/35 hover:text-white'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
            <span className="border border-white/15 px-4 py-2 text-sm uppercase tracking-[0.14em] text-brand-gray6">{username}</span>
            <button
              type="button"
              className="border border-brand-red bg-brand-red px-4 py-2 text-sm uppercase tracking-[0.14em] text-white transition hover:bg-transparent hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
              disabled={logoutBusy}
              onClick={async () => {
                setLogoutState(null);
                setLogoutBusy(true);
                try {
                  const result = await onLogout();
                  if (result === 'logout_403') {
                    setLogoutState(SESSION_SECURITY_MESSAGE);
                  } else if (result === 'logout_503' || result === 'network_error') {
                    setLogoutState('Выход временно недоступен.');
                  }
                } catch {
                  setLogoutState('Выход временно недоступен.');
                } finally {
                  setLogoutBusy(false);
                }
              }}
            >
              Выход
            </button>
          </div>
        </div>
        {logoutState ? <div className="border-t border-white/10 bg-brand-black px-5 py-3 text-center text-sm text-brand-gray6">{logoutState}</div> : null}
      </header>
      <main className="mx-auto max-w-7xl px-5 py-8 lg:px-8 lg:py-10">{children}</main>
    </div>
  );
}

type LogoutOutcome = 'signed_out' | 'session_missing' | 'logout_403' | 'logout_503' | 'network_error';

async function logoutAdminWithOutcome(): Promise<LogoutOutcome> {
  try {
    await logoutAdmin();
    return 'signed_out';
  } catch (error) {
    if (error instanceof AdminApiError) {
      if (error.status === 401) return 'session_missing';
      if (error.status === 403) return 'logout_403';
      if (error.status === 503) return 'logout_503';
    }
    return 'network_error';
  }
}

function AdminCenteredState({
  title,
  message,
  actionLabel,
  onAction,
}: {
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="grid min-h-screen place-items-center bg-brand-paper px-6 text-center text-brand-ink">
      <div className="max-w-lg rounded-3xl border border-brand-gray10/20 bg-white px-8 py-10 shadow-formal">
        <p className="text-xs uppercase tracking-[0.24em] text-brand-red">Admin</p>
        <h1 className="mt-4 font-display text-4xl">{title}</h1>
        <p className="mt-4 text-base leading-7 text-brand-ink/75">{message}</p>
        {actionLabel && onAction ? (
          <button
            type="button"
            className="mt-6 inline-flex items-center justify-center rounded-full border border-brand-red bg-brand-red px-6 py-3 text-sm font-semibold uppercase tracking-[0.14em] text-white transition hover:bg-transparent hover:text-brand-red"
            onClick={onAction}
          >
            {actionLabel}
          </button>
        ) : null}
      </div>
    </div>
  );
}
