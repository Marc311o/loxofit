import { Link, useParams } from "react-router";

export function ExerciseDetailDialog() {
  const { exerciseId } = useParams();
  return (
    <dialog open>
      <p>Exercise {exerciseId}</p>
      <Link to="..">Close</Link>
    </dialog>
  );
}
