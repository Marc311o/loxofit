import { Outlet } from "react-router";

export function AuthLayout() {
  return (
    <div style={{ maxWidth: 400, margin: "10vh auto" }}>
      <Outlet />
    </div>
  );
}
