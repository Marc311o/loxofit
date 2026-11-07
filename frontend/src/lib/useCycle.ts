import { useEffect, useState } from "react";

/** An index that advances every `intervalMs` and wraps at `length`; frozen while `paused`. */
export function useCycle(
  length: number,
  intervalMs: number,
  paused = false,
): number {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (paused || length < 2) return;
    const id = window.setInterval(
      () => setIndex((i) => (i + 1) % length),
      intervalMs,
    );
    return () => window.clearInterval(id);
  }, [length, intervalMs, paused]);

  return index;
}
