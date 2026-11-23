# Kody błędów

Każda odpowiedź z błędem ma postać `{"detail": ..., "code": ...}`; frontend tłumaczy pole `code`.

| Kod | HTTP | Znaczenie |
|---|---|---|
| `NOT_AUTHENTICATED` | 401 | Brak lub nieważny token dostępowy |
| `PERMISSION_DENIED` | 403 | Brak uprawnień |
| `NOT_FOUND` | 404 | Zasób nie istnieje lub nie należy do użytkownika |
| `CONFLICT` | 409 | Konflikt z bieżącym stanem zasobu |
| `VALIDATION_ERROR` | 422 | Treść lub parametry żądania nie przeszły walidacji |
| `INTERNAL_ERROR` | 500 | Nieoczekiwany błąd serwera |
| `SERVICE_UNAVAILABLE` | 503 | Usługa chwilowo niedostępna (np. brak połączenia z bazą) |
| `INVALID_CREDENTIALS` | 401 | Nieprawidłowy e-mail lub hasło |
| `INVALID_REFRESH_TOKEN` | 401 | Sesja wygasła - konieczne ponowne logowanie |
| `ACCOUNT_INACTIVE` | 403 | Konto jest nieaktywne |
| `PROFILE_NOT_FOUND` | 404 | Użytkownik nie uzupełnił jeszcze profilu |
| `EMAIL_TAKEN` | 409 | Konto z tym adresem e-mail już istnieje |
| `INVALID_EQUIPMENT` | 422 | Nieznany sprzęt |
| `EXERCISE_NOT_FOUND` | 404 | Ćwiczenie nie istnieje |
| `MODEL_CONFIG_NOT_FOUND` | 404 | Konfiguracja modelu nie istnieje |
| `DEFAULT_CONFIG_MISSING` | 500 | Brak domyślnej konfiguracji modelu |
| `NO_ACTIVE_PLAN` | 404 | Użytkownik nie ma aktywnego planu |
| `PLAN_NOT_FOUND` | 404 | Plan nie istnieje |
| `PLAN_ARCHIVED` | 409 | Zarchiwizowanego planu nie można zmieniać |
| `PLAN_INCOMPLETE` | 409 | Przed aktywacją trzeba wyliczyć wszystkie tygodnie planu |
| `UNSUPPORTED_CONFIG` | 409 | Konfiguracja modelu planu nie jest obsługiwana przez analizę |
| `INVALID_PLAN` | 422 | Niepoprawny plan |
| `GENERATION_NOT_FOUND` | 404 | Przebieg generowania nie istnieje |
| `GENERATION_ALREADY_SAVED` | 409 | Wygenerowany plan został już zapisany |
| `GENERATION_IN_PROGRESS` | 409 | Inne generowanie użytkownika wciąż trwa |
| `GENERATION_NOT_DONE` | 409 | Generowanie nie zakończyło się powodzeniem |
| `INVALID_GENERATION` | 422 | Niepoprawne żądanie generowania |
| `NO_EXERCISES_FOR_SESSION` | 422 | Dla jednej z sesji nie ma ćwiczenia pasującego do sprzętu użytkownika |
