import { MutationCache, QueryClient } from "@tanstack/react-query";

import { ApiError, errorMessage } from "@/lib/api";
import { toast } from "@/lib/toast";

declare module "@tanstack/react-query" {
  interface Register {
    mutationMeta: {
      silent?: boolean;
    };
  }
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      refetchOnWindowFocus: false,
      retry: (failureCount, error) =>
        !(error instanceof ApiError && error.status < 500) && failureCount < 2,
    },
  },
  mutationCache: new MutationCache({
    onError: (error, _variables, _context, mutation) => {
      if (!mutation.meta?.silent) toast.error(errorMessage(error));
    },
  }),
});
