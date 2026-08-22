import { useEffect, useState } from 'react';
import { AdminApiError, getCurrentAdmin } from './adminApi';
import { formatAdminError } from './adminMessages';

export type AdminSessionState =
  | { status: 'loading' }
  | { status: 'authenticated'; username: string }
  | { status: 'anonymous' }
  | { status: 'error'; message: string };

export function useAdminSession() {
  const [state, setState] = useState<AdminSessionState>({ status: 'loading' });
  const [retryIndex, setRetryIndex] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setState({ status: 'loading' });

    void getCurrentAdmin(controller.signal)
      .then((response) => {
        if (active) {
          setState({ status: 'authenticated', username: response.username });
        }
      })
      .catch((error: unknown) => {
        if (!active || controller.signal.aborted) {
          return;
        }
        if (error instanceof AdminApiError && (error.status === 401 || error.status === 403)) {
          setState({ status: 'anonymous' });
          return;
        }
        setState({ status: 'error', message: formatAdminError(error, 'session') });
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [retryIndex]);

  return {
    state,
    retry: () => setRetryIndex((value) => value + 1),
  };
}
