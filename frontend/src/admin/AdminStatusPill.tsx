import type { AdminCandidateStatus } from './adminApi';
import { ADMIN_CANDIDATE_STATUS_LABELS } from './adminStatus';

const STYLES: Record<AdminCandidateStatus, string> = {
  new: 'border-brand-red/25 bg-brand-red/10 text-brand-red',
  in_review: 'border-amber-300/40 bg-amber-50 text-amber-900',
  contacted: 'border-sky-300/40 bg-sky-50 text-sky-900',
  closed: 'border-emerald-300/40 bg-emerald-50 text-emerald-900',
  archived: 'border-brand-gray10/20 bg-brand-paperAlt text-brand-ink',
};

export function AdminStatusPill({ status }: { status: AdminCandidateStatus }) {
  return <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${STYLES[status]}`}>{ADMIN_CANDIDATE_STATUS_LABELS[status]}</span>;
}
