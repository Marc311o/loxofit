# API map

All paths are under `/api/v1`. Every endpoint needs a JWT access token unless marked otherwise; errors are `{"detail": ..., "code": ...}` (see `errors.en.md`).

## Health

| Method | Path | Description | Responses |
|---|---|---|---|
| `GET` | `/health` ¹ | Checks the API and its database connection | 200, 503 |

## Authentication

| Method | Path | Description | Responses |
|---|---|---|---|
| `POST` | `/auth/register` ¹ | Creates an account | 201, 409, 422 |
| `POST` | `/auth/refresh` ¹ | Issues a new access token from the refresh cookie | 200, 401, 422 |
| `POST` | `/auth/login` ¹ | Logs in; returns an access token and sets the refresh cookie | 200, 401, 403, 422 |
| `POST` | `/auth/logout` ¹ | Revokes the refresh token | 204, 422 |
| `GET` | `/auth/me` | The logged-in user | 200, 401 |

## Catalog

| Method | Path | Description | Responses |
|---|---|---|---|
| `GET` | `/muscles` | Muscles with their groups | 200, 401 |
| `GET` | `/equipment` | Equipment, filtered by category | 200, 401, 422 |
| `GET` | `/exercises` | Exercises - filters, search, pagination | 200, 401, 422 |
| `GET` | `/exercises/group-counts` | Exercises per muscle group for the given filters | 200, 401, 422 |
| `GET` | `/exercises/{exercise_id}` | Exercise details: muscle roles, equipment, substitutes | 200, 401, 422 |

## Generator

| Method | Path | Description | Responses |
|---|---|---|---|
| `POST` | `/generator/runs` | Starts generating a plan in the background | 202, 401, 404, 409, 422 |
| `GET` | `/generator/runs/{run_id}` | Status, progress and result of a generation | 200, 401, 404, 422 |
| `GET` | `/generator/runs/{run_id}/analysis` | Analysis of the generated plan | 200, 401, 404, 409, 422 |
| `POST` | `/generator/runs/{run_id}/plan` | Saves the generated plan as a draft | 201, 401, 404, 409, 422 |

## Plans

| Method | Path | Description | Responses |
|---|---|---|---|
| `GET` | `/plans` | The user's plans | 200, 401, 404 |
| `POST` | `/plans` | Creates an empty draft plan | 201, 401, 404, 422 |
| `GET` | `/plans/active` | The active plan | 200, 401, 404 |
| `GET` | `/plans/{plan_id}` | A plan with its weeks, sessions and exercises | 200, 401, 404, 422 |
| `PATCH` | `/plans/{plan_id}` | Changes the name or the number of weeks | 200, 401, 404, 409, 422 |
| `DELETE` | `/plans/{plan_id}` | Deletes a plan | 204, 401, 404, 422 |
| `POST` | `/plans/{plan_id}/activate` | Makes the plan the active one | 200, 401, 404, 409, 422 |
| `PUT` | `/plans/{plan_id}/base-week` | Replaces the base week (week 1) | 200, 401, 404, 409, 422 |
| `PUT` | `/plans/{plan_id}/muscle-targets` | Sets muscle priorities | 200, 401, 404, 409, 422 |
| `POST` | `/plans/{plan_id}/progression` | Computes weeks 2..n from the base week | 200, 401, 404, 409, 422 |
| `GET` | `/plans/{plan_id}/analysis` | Scores the plan: volume per muscle, time, issues | 200, 401, 404, 409, 422 |

## Users

| Method | Path | Description | Responses |
|---|---|---|---|
| `PATCH` | `/users/me` | Changes the account data | 200, 401, 422 |
| `GET` | `/users/me/profile` | The training profile | 200, 401, 404 |
| `PUT` | `/users/me/profile` | Creates or replaces the training profile | 200, 401, 422 |
| `GET` | `/users/me/equipment` | The equipment the user has | 200, 401 |
| `PUT` | `/users/me/equipment` | Replaces the user's equipment | 200, 401, 422 |

¹ Public - no access token needed.
