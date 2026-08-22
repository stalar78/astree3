import type { AdminCandidateStatus } from './adminApi';

export const ADMIN_CANDIDATE_STATUS_LABELS: Record<AdminCandidateStatus, string> = {
  new: 'Новая',
  in_review: 'На рассмотрении',
  contacted: 'Связались',
  closed: 'Закрыта',
  archived: 'Архив',
};
