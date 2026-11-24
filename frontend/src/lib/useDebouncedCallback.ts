import { useCallback, useEffect, useRef } from "react";

export function useDebouncedCallback<Args extends unknown[]>(
  callback: (...args: Args) => void,
  delayMs = 300,
): [debounced: (...args: Args) => void, cancel: () => void] {
  const timer = useRef<number | undefined>(undefined);

  const cancel = useCallback(() => window.clearTimeout(timer.current), []);

  const debounced = useCallback(
    (...args: Args) => {
      window.clearTimeout(timer.current);
      timer.current = window.setTimeout(() => callback(...args), delayMs);
    },
    [callback, delayMs],
  );

  useEffect(() => cancel, [cancel]);

  return [debounced, cancel];
}
