# Error codes

Every error response is `{"detail": ..., "code": ...}`; the frontend translates the `code`.

| Code | HTTP | Meaning |
|---|---|---|
| `NOT_AUTHENTICATED` | 401 | Failed to authenticate |
| `PERMISSION_DENIED` | 403 | Insufficient permission |
| `NOT_FOUND` | 404 | Asset not found |
| `CONFLICT` | 409 | Conflict with actual state of the asset |
| `VALIDATION_ERROR` | 422 | The request body or parameters failed validation |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
| `INVALID_CREDENTIALS` | 401 | Invalid email or password |
| `INVALID_REFRESH_TOKEN` | 401 | Session expired, proceed to log in again |
| `ACCOUNT_INACTIVE` | 403 | The account is inactive |
| `PROFILE_NOT_FOUND` | 404 | User profile not set up yet |
| `EMAIL_TAKEN` | 409 | Account with this email address already exists |
| `INVALID_EQUIPMENT` | 422 | Unknown equipment |
| `EXERCISE_NOT_FOUND` | 404 | Exercise not found |
| `MODEL_CONFIG_NOT_FOUND` | 404 | Model config not found |
| `DEFAULT_CONFIG_MISSING` | 500 | Default model configuration is not available |
| `NO_ACTIVE_PLAN` | 404 | No active plan |
| `PLAN_NOT_FOUND` | 404 | Plan not found |
| `PLAN_ARCHIVED` | 409 | Archived plan cannot be modified |
| `PLAN_INCOMPLETE` | 409 | All weeks of the plan must be generated before activation |
| `UNSUPPORTED_CONFIG` | 409 | The plan's model config is not supported by the analysis |
| `INVALID_PLAN` | 422 | Invalid plan |
| `GENERATION_NOT_FOUND` | 404 | Generation run not found |
| `GENERATION_ALREADY_SAVED` | 409 | This generated plan has already been saved |
| `GENERATION_IN_PROGRESS` | 409 | Another generation is still running |
| `GENERATION_NOT_DONE` | 409 | The generation has not finished successfully |
| `INVALID_GENERATION` | 422 | Invalid generation request |
| `NO_EXERCISES_FOR_SESSION` | 422 | No exercise with the user's equipment fits one of the sessions |
