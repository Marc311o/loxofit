import { Navigate, Outlet } from "react-router";

import { FullScreenLoader } from "@/components/FullScreenLoader";
import { useCurrentUser } from "@/features/auth/api";

export function GuestOnly() {
  const user = useCurrentUser();
  if (user.isPending) return <FullScreenLoader />;
  return user.isSuccess ? <Navigate to="/" replace /> : <Outlet />;
}
