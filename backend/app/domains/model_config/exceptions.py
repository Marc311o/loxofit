from app.core.errors import AppError


class DefaultConfigMissingError(AppError):
    code = "DEFAULT_CONFIG_MISSING"
    detail = "Default model configuration is not available"
