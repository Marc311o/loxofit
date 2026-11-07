import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./queryClient.ts";
import { RouterProvider } from "react-router/dom";
import { router } from "./router.tsx";
import { ThemeProvider } from "@/styles/ThemeProvider.tsx";
import { ToastHost } from "@/components/ToastHost.tsx";

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <RouterProvider router={router} />
        <ToastHost />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
