import { Navigate, Outlet, useLocation } from "react-router";

import { FullScreenLoader } from "@/components/FullScreenLoader";
import { useCurrentUser } from "@/features/auth/api";
import { SessionExpiredDialog } from "@/features/auth/components/SessionExpiredDialog";

export function RequireAuth() {
  const location = useLocation();
  const user = useCurrentUser();

  if (user.isPending) return <FullScreenLoader />;
  if (user.isError)
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;

  return (
    <>
      <Outlet />
      <SessionExpiredDialog />
    </>
  );
}
