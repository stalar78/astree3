import { isHostingEdition } from '../config/edition';

export const candidateFormEnabled =
  !isHostingEdition && import.meta.env.VITE_CANDIDATE_FORM_ENABLED === 'true';
