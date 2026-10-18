import { NavLink, Outlet } from "react-router";

export function AppLayout() {
  return (
    <>
      <nav>
        <NavLink to="/" end>
          Start
        </NavLink>{" "}
        | <NavLink to="/catalog">Catalog</NavLink> |{" "}
        <NavLink to="/plan">Plan</NavLink> |{" "}
        <NavLink to="/profile">Profile</NavLink>
      </nav>
      <main>
        <Outlet />
      </main>
    </>
  );
}
