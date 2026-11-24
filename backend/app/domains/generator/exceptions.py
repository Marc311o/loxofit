from app.core.errors import AppError, ConflictError, NotFoundError


class GenerationNotFoundError(NotFoundError):
    code = "GENERATION_NOT_FOUND"
    detail = "Generation run not found"


class GenerationInProgressError(ConflictError):
    code = "GENERATION_IN_PROGRESS"
    detail = "Another generation is still running"


class GenerationNotDoneError(ConflictError):
    code = "GENERATION_NOT_DONE"
    detail = "The generation has not finished successfully"


class GenerationAlreadySavedError(ConflictError):
    code = "GENERATION_ALREADY_SAVED"
    detail = "This generated plan has already been saved"


class InvalidGenerationError(AppError):
    status_code = 422
    code = "INVALID_GENERATION"
    detail = "Invalid generation request"


class NoExercisesForSessionError(InvalidGenerationError):
    """No exercise fits a session's focus with the user's equipment."""

    code = "NO_EXERCISES_FOR_SESSION"
