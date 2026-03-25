import { useState, useEffect, useCallback } from 'react';

interface UseApiQueryReturn<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useApiQuery = <T,>(
  queryFn: () => Promise<T>,
  dependencies: unknown[] = [],
  options: { enabled?: boolean; retryCount?: number; retryDelay?: number } = {}
): UseApiQueryReturn<T> => {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const { enabled = true, retryCount: maxRetries = 3, retryDelay = 1000 } = options;

  const fetchData = useCallback(async (): Promise<void> => {
    if (!enabled) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await queryFn();
      setData(result);
      setError(null);
      setRetryCount(0);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';

      if (retryCount < maxRetries) {
        setTimeout(() => {
          setRetryCount((prev) => prev + 1);
        }, retryDelay);
      } else {
        setError(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  }, [queryFn, enabled, retryCount, maxRetries, retryDelay]);

  useEffect(() => {
    fetchData();
  }, [fetchData, ...dependencies]);

  const refetch = useCallback(async (): Promise<void> => {
    setRetryCount(0);
    await fetchData();
  }, [fetchData]);

  return {
    data,
    isLoading,
    error,
    refetch,
  };
};
