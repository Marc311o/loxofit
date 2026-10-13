from app.core.errors import NotFoundError


class ExerciseNotFoundError(NotFoundError):
    code = "EXERCISE_NOT_FOUND"
    detail = "Exercise not found"
