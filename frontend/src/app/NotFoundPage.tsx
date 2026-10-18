import { Link } from "react-router";

export function NotFoundPage() {
  return (
    <>
      <h1>404</h1>
      <Link to="/">Back to start</Link>
    </>
  );
}
