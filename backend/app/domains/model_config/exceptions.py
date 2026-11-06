from app.core.errors import AppError, NotFoundError


class DefaultConfigMissingError(AppError):
    code = "DEFAULT_CONFIG_MISSING"
    detail = "Default model configuration is not available"


class ModelConfigNotFoundError(NotFoundError):
    code = "MODEL_CONFIG_NOT_FOUND"
    detail = "Model config not found"
