import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "../lib/queryClient.ts";
import { RouterProvider } from "react-router/dom";
import { router } from "./router.tsx";

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
