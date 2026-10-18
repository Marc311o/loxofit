import { NavLink, Outlet } from "react-router";

export function CatalogLayout() {
  return (
    <>
      <nav>
        <NavLink to="exercises">Exercises</NavLink> |{" "}
        <NavLink to="muscles">Muscles</NavLink> |{" "}
        <NavLink to="equipment">Equipment</NavLink>
      </nav>
      <Outlet />
    </>
  );
}
