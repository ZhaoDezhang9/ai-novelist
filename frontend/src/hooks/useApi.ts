import { useState, useEffect, useRef } from "react";

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useApi<T>(
  fetchFn: (signal: AbortSignal) => Promise<T>,
  deps: unknown[] = []
): UseApiState<T> & { refetch: () => void } {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(false);
  const seqRef = useRef(0);

  const execute = async () => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const seq = ++seqRef.current;

    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn(controller.signal);
      if (!controller.signal.aborted && seq === seqRef.current) {
        if (mountedRef.current) { setData(result); setLoading(false); }
        else { setData(result); }
      }
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      if (!controller.signal.aborted && seq === seqRef.current) {
        const msg = e instanceof Error ? e.message : "请求失败";
        if (mountedRef.current) { setError(msg); setLoading(false); }
        else { setError(msg); }
      }
    }
  };

  useEffect(() => {
    mountedRef.current = true;
    execute();
    return () => {
      mountedRef.current = false;
      abortRef.current?.abort();
    };
  }, deps);

  return { data, loading, error, refetch: execute };
}
