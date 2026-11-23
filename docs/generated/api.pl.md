# Mapa API

Wszystkie ścieżki mają prefiks `/api/v1`. Każdy endpoint poza oznaczonymi wymaga tokenu dostępowego JWT; błędy mają postać `{"detail": ..., "code": ...}` (zob. `errors.pl.md`).

## Stan usługi

| Metoda | Ścieżka | Opis | Odpowiedzi |
|---|---|---|---|
| `GET` | `/health` ¹ | Sprawdza działanie API i połączenie z bazą | 200, 503 |

## Uwierzytelnianie

| Metoda | Ścieżka | Opis | Odpowiedzi |
|---|---|---|---|
| `POST` | `/auth/register` ¹ | Zakłada konto | 201, 409, 422 |
| `POST` | `/auth/refresh` ¹ | Wydaje nowy token dostępowy na podstawie ciasteczka odświeżającego | 200, 401, 422 |
| `POST` | `/auth/login` ¹ | Logowanie; zwraca token dostępowy i ustawia ciasteczko odświeżające | 200, 401, 403, 422 |
| `POST` | `/auth/logout` ¹ | Unieważnia token odświeżający | 204, 422 |
| `GET` | `/auth/me` | Zalogowany użytkownik | 200, 401 |

## Katalog

| Metoda | Ścieżka | Opis | Odpowiedzi |
|---|---|---|---|
| `GET` | `/muscles` | Mięśnie wraz z grupami | 200, 401 |
| `GET` | `/equipment` | Sprzęt, z filtrowaniem po kategorii | 200, 401, 422 |
| `GET` | `/exercises` | Ćwiczenia - filtry, wyszukiwanie, stronicowanie | 200, 401, 422 |
| `GET` | `/exercises/group-counts` | Liczba ćwiczeń w grupach mięśniowych dla podanych filtrów | 200, 401, 422 |
| `GET` | `/exercises/{exercise_id}` | Szczegóły ćwiczenia: role mięśni, sprzęt, zamienniki | 200, 401, 422 |

## Generator

| Metoda | Ścieżka | Opis | Odpowiedzi |
|---|---|---|---|
| `POST` | `/generator/runs` | Uruchamia generowanie planu w tle | 202, 401, 404, 409, 422 |
| `GET` | `/generator/runs/{run_id}` | Stan, postęp i wynik generowania | 200, 401, 404, 422 |
| `GET` | `/generator/runs/{run_id}/analysis` | Analiza wygenerowanego planu | 200, 401, 404, 409, 422 |
| `POST` | `/generator/runs/{run_id}/plan` | Zapisuje wygenerowany plan jako szkic | 201, 401, 404, 409, 422 |

## Plany

| Metoda | Ścieżka | Opis | Odpowiedzi |
|---|---|---|---|
| `GET` | `/plans` | Plany użytkownika | 200, 401, 404 |
| `POST` | `/plans` | Tworzy pusty szkic planu | 201, 401, 404, 422 |
| `GET` | `/plans/active` | Aktywny plan | 200, 401, 404 |
| `GET` | `/plans/{plan_id}` | Plan z tygodniami, sesjami i ćwiczeniami | 200, 401, 404, 422 |
| `PATCH` | `/plans/{plan_id}` | Zmienia nazwę lub liczbę tygodni | 200, 401, 404, 409, 422 |
| `DELETE` | `/plans/{plan_id}` | Usuwa plan | 204, 401, 404, 422 |
| `POST` | `/plans/{plan_id}/activate` | Ustawia plan jako aktywny | 200, 401, 404, 409, 422 |
| `PUT` | `/plans/{plan_id}/base-week` | Zastępuje tydzień bazowy (tydzień 1) | 200, 401, 404, 409, 422 |
| `PUT` | `/plans/{plan_id}/muscle-targets` | Ustawia priorytety mięśni | 200, 401, 404, 409, 422 |
| `POST` | `/plans/{plan_id}/progression` | Wylicza tygodnie 2..n z tygodnia bazowego | 200, 401, 404, 409, 422 |
| `GET` | `/plans/{plan_id}/analysis` | Ocenia plan: objętość na mięsień, czas, problemy | 200, 401, 404, 409, 422 |

## Użytkownicy

| Metoda | Ścieżka | Opis | Odpowiedzi |
|---|---|---|---|
| `PATCH` | `/users/me` | Zmienia dane konta | 200, 401, 422 |
| `GET` | `/users/me/profile` | Profil treningowy | 200, 401, 404 |
| `PUT` | `/users/me/profile` | Tworzy lub zastępuje profil treningowy | 200, 401, 422 |
| `GET` | `/users/me/equipment` | Sprzęt użytkownika | 200, 401 |
| `PUT` | `/users/me/equipment` | Zastępuje sprzęt użytkownika | 200, 401, 422 |

¹ Publiczny - nie wymaga tokenu dostępowego.
