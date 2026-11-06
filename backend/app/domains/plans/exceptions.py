from app.core.errors import AppError, ConflictError, NotFoundError


class PlanNotFoundError(NotFoundError):
    code = "PLAN_NOT_FOUND"
    detail = "Plan not found"


class NoActivePlanError(NotFoundError):
    code = "NO_ACTIVE_PLAN"
    detail = "No active plan"


class PlanArchivedError(ConflictError):
    code = "PLAN_ARCHIVED"
    detail = "Archived plan cannot be modified"


class PlanIncompleteError(ConflictError):
    code = "PLAN_INCOMPLETE"
    detail = "All weeks of the plan must be generated before activation"


class InvalidPlanError(AppError):
    status_code = 422
    code = "INVALID_PLAN"
    detail = "Invalid plan"
