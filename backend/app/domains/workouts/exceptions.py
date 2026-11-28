from app.core.errors import ConflictError, NotFoundError


class WorkoutNotFoundError(NotFoundError):
    code = "WORKOUT_NOT_FOUND"
    detail = "Workout not found"


class NoWorkoutInProgressError(NotFoundError):
    code = "NO_WORKOUT_IN_PROGRESS"
    detail = "No workout in progress"


class SessionNotFoundError(NotFoundError):
    code = "SESSION_NOT_FOUND"
    detail = "No such session in the active plan"


class LoggedExerciseNotFoundError(NotFoundError):
    code = "LOGGED_EXERCISE_NOT_FOUND"
    detail = "No such exercise in the workout"


class SetNotFoundError(NotFoundError):
    code = "SET_NOT_FOUND"
    detail = "No such set"


class WorkoutInProgressError(ConflictError):
    code = "WORKOUT_IN_PROGRESS"
    detail = "Another workout is in progress - finish or abandon it first"


class WorkoutNotInProgressError(ConflictError):
    code = "WORKOUT_NOT_IN_PROGRESS"
    detail = "The workout is over and cannot be changed"


class SessionAlreadyDoneError(ConflictError):
    code = "SESSION_ALREADY_DONE"
    detail = "This session has already been done or skipped"


class ExerciseHasSetsError(ConflictError):
    code = "EXERCISE_HAS_SETS"
    detail = "An exercise with logged sets cannot be replaced"


class WorkoutEmptyError(ConflictError):
    code = "WORKOUT_EMPTY"
    detail = "A workout without sets cannot be finished - abandon it instead"
