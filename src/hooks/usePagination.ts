import { useState, useCallback } from 'react';

interface UsePaginationReturn {
  page: number;
  pageSize: number;
  goToPage: (page: number) => void;
  nextPage: () => void;
  prevPage: () => void;
  setPageSize: (size: number) => void;
  reset: () => void;
}

export const usePagination = (initialPage: number = 1, initialPageSize: number = 10): UsePaginationReturn => {
  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSizeState] = useState(initialPageSize);

  const goToPage = useCallback((newPage: number): void => {
    if (newPage >= 1) {
      setPage(newPage);
    }
  }, []);

  const nextPage = useCallback((): void => {
    setPage((prev) => prev + 1);
  }, []);

  const prevPage = useCallback((): void => {
    setPage((prev) => (prev > 1 ? prev - 1 : prev));
  }, []);

  const setPageSize = useCallback((size: number): void => {
    if (size > 0) {
      setPageSizeState(size);
      setPage(1);
    }
  }, []);

  const reset = useCallback((): void => {
    setPage(initialPage);
    setPageSizeState(initialPageSize);
  }, [initialPage, initialPageSize]);

  return {
    page,
    pageSize,
    goToPage,
    nextPage,
    prevPage,
    setPageSize,
    reset,
  };
};
