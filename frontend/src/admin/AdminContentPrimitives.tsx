import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

export function AdminNotice({ children, tone = 'error' }: { children: ReactNode; tone?: 'error' | 'info' }) {
  return (
    <div className={`border px-4 py-3 text-sm leading-6 ${tone === 'error' ? 'border-brand-red/30 bg-brand-red/10' : 'border-brand-gray10/20 bg-brand-paper'}`} role={tone === 'error' ? 'alert' : 'status'}>
      {children}
    </div>
  );
}

export function AdminLoadingState({ label = 'Загрузка...' }: { label?: string }) {
  return <AdminNotice tone="info">{label}</AdminNotice>;
}

export function AdminContentEmpty({ children }: { children: ReactNode }) {
  return <div className="border border-brand-gray10/20 bg-white px-6 py-12 text-center text-sm text-brand-ink/70">{children}</div>;
}

export function AdminPublicationStatus({ published }: { published: boolean }) {
  return (
    <span className={`inline-flex border px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] ${published ? 'border-brand-red/40 bg-brand-red/10 text-brand-red' : 'border-brand-gray10/30 bg-brand-paper text-brand-ink/65'}`}>
      {published ? 'Опубликовано' : 'Черновик'}
    </span>
  );
}

export function AdminBackLink({ to, children = 'К списку' }: { to: string; children?: ReactNode }) {
  return <Link to={to} className="text-sm font-semibold uppercase tracking-[0.14em] text-brand-ink/60 transition hover:text-brand-red">← {children}</Link>;
}

export function AdminField({ label, required, help, children }: { label: string; required?: boolean; help?: string; children: ReactNode }) {
  return (
    <label className="grid gap-2 text-sm font-semibold text-brand-ink">
      <span>{label}{required ? <span className="text-brand-red"> *</span> : null}</span>
      {children}
      {help ? <span className="text-xs font-normal leading-5 text-brand-ink/60">{help}</span> : null}
    </label>
  );
}

export function AdminInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`w-full border border-brand-gray10/25 bg-brand-paper px-4 py-3 text-base outline-none transition focus:border-brand-red focus:ring-2 focus:ring-brand-red/20 disabled:cursor-not-allowed disabled:opacity-60 ${props.className ?? ''}`} />;
}

export function AdminTextarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={`min-h-32 w-full resize-y border border-brand-gray10/25 bg-brand-paper px-4 py-3 text-base leading-7 outline-none transition focus:border-brand-red focus:ring-2 focus:ring-brand-red/20 disabled:cursor-not-allowed disabled:opacity-60 ${props.className ?? ''}`} />;
}

export function AdminSaveButton({ busy }: { busy: boolean }) {
  return <button type="submit" disabled={busy} className="border border-brand-red bg-brand-red px-6 py-3 text-sm font-semibold uppercase tracking-[0.14em] text-white transition hover:bg-transparent hover:text-brand-red disabled:cursor-not-allowed disabled:opacity-60">{busy ? 'Сохранение...' : 'Сохранить'}</button>;
}

export function AdminDeleteControl({ armed, busy, onArm, onConfirm, onCancel }: { armed: boolean; busy: boolean; onArm: () => void; onConfirm: () => void; onCancel: () => void }) {
  if (!armed) {
    return <button type="button" disabled={busy} onClick={onArm} className="border border-brand-red/50 px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] text-brand-red transition hover:bg-brand-red hover:text-white disabled:opacity-50">Удалить</button>;
  }
  return (
    <div className="flex flex-wrap items-center gap-3 border border-brand-red/30 bg-brand-red/10 p-3">
      <span className="text-sm font-semibold">Подтвердить удаление?</span>
      <button type="button" disabled={busy} onClick={onConfirm} className="border border-brand-red bg-brand-red px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-white disabled:opacity-50">{busy ? 'Удаление...' : 'Подтвердить'}</button>
      <button type="button" disabled={busy} onClick={onCancel} className="border border-brand-gray10/30 px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-brand-ink disabled:opacity-50">Отмена</button>
    </div>
  );
}

export function AdminMeta({ items }: { items: Array<[string, string | null | undefined]> }) {
  return <dl className="grid gap-3 border-t border-brand-gray10/15 pt-5 text-sm md:grid-cols-3">{items.map(([label, value]) => <div key={label}><dt className="text-xs uppercase tracking-[0.12em] text-brand-ink/55">{label}</dt><dd className="mt-1 text-brand-ink/80">{value ?? '—'}</dd></div>)}</dl>;
}
