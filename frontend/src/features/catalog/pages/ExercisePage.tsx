import { Link, Outlet } from "react-router";

export function ExercisesPage() {
  return (
    <>
      <h1>Exercises</h1>
      <ul>
        <li>
          <Link to="1">Exercise 1</Link>
        </li>
        <li>
          <Link to="2">Exercise 2</Link>
        </li>
      </ul>
      <Outlet />
    </>
  );
}
