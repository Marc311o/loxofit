export type ToastSeverity = "success" | "info" | "warning" | "error";
export type Toast = { id: number; message: string; severity: ToastSeverity };

type Listener = (toast: Toast) => void;
const listeners = new Set<Listener>();
let nextId = 1;

function emit(message: string, severity: ToastSeverity) {
  const item = { id: nextId++, message, severity };
  listeners.forEach((listener) => listener(item));
}

/** Callable from anywhere - components, hooks, the query client. */
export const toast = {
  success: (message: string) => emit(message, "success"),
  info: (message: string) => emit(message, "info"),
  warning: (message: string) => emit(message, "warning"),
  error: (message: string) => emit(message, "error"),
};

export function onToast(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
