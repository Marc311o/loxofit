import { Navigate, Outlet } from "react-router";

import { FullScreenLoader } from "@/components/FullScreenLoader";
import { useMyProfile } from "../api";

/**
 * Onboarding comes first: without a profile (saved at its end) the app sends
 * the user there. If the profile cannot be loaded the app still opens.
 */
export function RequireProfile() {
  const profile = useMyProfile();

  if (profile.isPending) return <FullScreenLoader />;
  if (profile.data === null) return <Navigate to="/onboarding" replace />;
  return <Outlet />;
}
