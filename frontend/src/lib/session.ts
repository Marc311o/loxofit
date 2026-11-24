let accessToken: string | null = null;

export const session = {
  getAccessToken: () => accessToken,
  setAccessToken: (token: string) => {
    accessToken = token;
  },
  clear: () => {
    accessToken = null;
  },
};

type Listener = () => void;
const expiredListeners = new Set<Listener>();

export function onSessionExpired(listener: Listener): () => void {
  expiredListeners.add(listener);
  return () => {
    expiredListeners.delete(listener);
  };
}

export function notifySessionExpired(): void {
  expiredListeners.forEach((listener) => listener());
}
