import { useEffect, useState } from 'react';

import { PublicContentApiError, getPublicPage, type PublicPage } from './publicContentApi';

type ManagedPageState = {
  status: 'loading' | 'ready' | 'not_found' | 'error';
  page: PublicPage | null;
  retry: () => void;
};

export function usePublicManagedPage(pageKey: string): ManagedPageState {
  const [retryToken, setRetryToken] = useState(0);
  const [page, setPage] = useState<PublicPage | null>(null);
  const [status, setStatus] = useState<ManagedPageState['status']>('loading');

  useEffect(() => {
    const controller = new AbortController();
    setStatus('loading');
    setPage(null);

    void getPublicPage(pageKey, controller.signal)
      .then((result) => {
        setPage(result);
        setStatus('ready');
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') {
          return;
        }
        if (error instanceof PublicContentApiError && error.status === 404) {
          setStatus('not_found');
          return;
        }
        setStatus('error');
      });

    return () => controller.abort();
  }, [pageKey, retryToken]);

  return {
    status,
    page,
    retry: () => setRetryToken((value) => value + 1),
  };
}
