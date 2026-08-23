const CANDIDATE_APPLICATIONS_ROOT = '/api/v1/candidate-applications';

export type CandidateAcceptedResponse = {
  accepted: true;
};

export class CandidateApiError extends Error {
  readonly status: number;

  constructor(status: number) {
    super('Candidate application request failed');
    this.name = 'CandidateApiError';
    this.status = status;
  }
}

export async function submitCandidateApplication(formData: FormData, signal?: AbortSignal): Promise<CandidateAcceptedResponse> {
  const response = await fetch(CANDIDATE_APPLICATIONS_ROOT, {
    method: 'POST',
    body: formData,
    credentials: 'same-origin',
    signal,
  });

  if (response.status !== 201) {
    throw new CandidateApiError(response.status);
  }

  const parsed = await response.json().catch(() => undefined);
  if (!isAcceptedResponse(parsed)) {
    throw new CandidateApiError(response.status);
  }

  return parsed;
}

function isAcceptedResponse(value: unknown): value is CandidateAcceptedResponse {
  return typeof value === 'object' && value !== null && (value as { accepted?: unknown }).accepted === true;
}
