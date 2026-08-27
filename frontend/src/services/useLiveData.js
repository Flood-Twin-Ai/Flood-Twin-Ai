import { useEffect, useState } from "react";

/**
 * Calls `fetcher()` (an async function returning { data }) once on mount.
 * If it fails (backend not running yet — common during frontend-first dev),
 * falls back to `mockValue` so the UI stays fully demoable.
 *
 * Returns { data, loading, isMock, refetch }
 */
export function useLiveData(fetcher, mockValue, deps = []) {
  const [data, setData] = useState(mockValue);
  const [loading, setLoading] = useState(true);
  const [isMock, setIsMock] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetcher();
      setData(res.data);
      setIsMock(false);
    } catch (err) {
      setData(mockValue);
      setIsMock(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, isMock, refetch: load };
}
