import type { ReactNode } from 'react';
import { useNavigate, useLocation, Outlet, Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { AdminApiError, logoutAdmin } from './adminApi';
import { formatAdminError } from './adminMessages';
import { useAdminSession } from './useAdminSession';

export function AdminProtectedLayout() {
  const session = useAdminSession();
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
    return <AdminCenteredState title="Admin недоступен" message={session.message} />;
  }

  if (session.status !== 'authenticated') {
    return null;
  }

  return (
    <AdminShell
      username={session.username}
      onLogout={async () => {
        try {
          await logoutAdmin();
        } catch (error) {
          if (error instanceof AdminApiError && (error.status === 401 || error.status === 403)) {
            navigate('/admin/login', { replace: true });
            return;
          }
          throw error;
        }
        navigate('/admin/login', { replace: true });
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
  onLogout: () => Promise<void>;
  children: ReactNode;
}) {
  const [logoutState, setLogoutState] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(218,41,28,0.08),transparent_30%),linear-gradient(180deg,#f4f0e8_0%,#efe8dc_100%)] text-brand-ink">
      <header className="border-b border-brand-gray10/20 bg-brand-black text-white shadow-formal">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-5 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-brand-gray6">Admin console</p>
            <h1 className="font-display text-3xl">Управление кандидатами</h1>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Link to="/admin/candidates" className="rounded-full border border-white/15 px-4 py-2 text-sm uppercase tracking-[0.14em] text-white/90 transition hover:border-white/35 hover:text-white">
              Кандидаты
            </Link>
            <span className="rounded-full border border-white/15 px-4 py-2 text-sm uppercase tracking-[0.14em] text-brand-gray6">
              {username}
            </span>
            <button
              type="button"
              className="rounded-full border border-brand-red bg-brand-red px-4 py-2 text-sm uppercase tracking-[0.14em] text-white transition hover:bg-transparent hover:text-white"
              onClick={async () => {
                try {
                  setLogoutState(null);
                  await onLogout();
                } catch (error) {
                  setLogoutState(formatAdminError(error, 'logout'));
                }
              }}
            >
              Выход
            </button>
          </div>
        </div>
        {logoutState ? (
          <div className="border-t border-white/10 bg-brand-black/80 px-5 py-3 text-center text-sm text-brand-gray6">{logoutState}</div>
        ) : null}
      </header>
      <main className="mx-auto max-w-7xl px-5 py-8 lg:px-8 lg:py-10">{children}</main>
    </div>
  );
}

function AdminCenteredState({ title, message }: { title: string; message: string }) {
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
