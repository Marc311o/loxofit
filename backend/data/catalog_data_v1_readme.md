# Dane startowe – `catalog_seed.xlsx`

Uzasadnienie danych w `aktywacja_miesni_EMG.xlsx`.
## Kolory komórek

| Kolor | Znaczenie                               |
|---|-----------------------------------------|
| turkusowy | przepisane z arkusza badawczego (pewne) |
| żółty | wstępna propozycja                      |
| biały | puste, do uzupełnienia                  |

## Klucze naturalne

Seed rozpoznaje istniejące wiersze po kluczach, a nie po id (id nadaje baza):

| Arkusz | Klucz |
|---|---|
| `muscles` | `code` |
| `equipment` | `name_en` |
| `exercises` | `name_en` |


## Arkusze

### `muscles`

| Kolumna | Opis |
|---|---|
| `code` | klucz, maks. 10 znaków |
| `name_en`, `name_pl` | nazwy |
| `muscle_group` | `chest`, `back`, `shoulders`, `arms`, `core`, `glutes`, `thighs`, `calves` |
| `is_volume_target` | `FALSE` = mięsień nie jest celem optymalizacji objętości (np. `erectors`: brak progów w źródłach) |
| `description_en`, `description_pl` | opcjonalne |

### `equipment`

| Kolumna | Opis |
|---|---|
| `name_en` | klucz |
| `name_pl` | nazwa |
| `category` | `free_weights`, `station`, `cable`, `machine` |
| `description_en`, `description_pl` | opcjonalne |

### `exercises`

| Kolumna | Opis                                                                                                     |
|---|----------------------------------------------------------------------------------------------------------|
| `name_en` | klucz                                                                                                    |
| `name_pl` | nazwa                                                                                                    |
| `main_group` | grupa mięśniowa, pod którą ćwiczenie widnieje w katalogu                                                 |
| `movement_pattern` | wzorzec ruchu (18 wartości, np. `horizontal_push`, `hip_hinge`, `lunge`)                                 |
| `is_compound` | ćwiczenie wielostawowe                                                                                   |
| `is_unilateral` | ćwiczenie jednostronne                                                                                   |
| `fatigue_cost` | 1–5                                                                                                      |
| `complexity` | 1–5                                                                                                      |
| `default_tempo` | 4 znaki, np. `3010` (ekscentryka, pauza rozciągnięcie, koncentryka, pauza spięcie); puste = brak zaleceń |
| `instructions_en`, `instructions_pl` | opcjonalne                                                                                               |

**`fatigue_cost` (1–5):**
- 1 = izolacja na maszynie, małe mięśnie;
- 3 = ćwiczenie wielostawowe bez obciążenia osiowego;
- 5 = ciężkie ćwiczenie wielostawowe z obciążeniem osiowym.

**`complexity` (1–5):**
- 1 = maszyna, stały tor ruchu;
- 3 = sztanga, typowa technika;
- 5 = wysokie wymagania mobilności i stabilizacji.

### `exercise_muscles`

| Kolumna | Opis |
|---|---|
| `exercise` | `name_en` ćwiczenia |
| `muscle` | `code` mięśnia |
| `role` | `primary`, `secondary`, `stabilizer` |

Role pochodzą z arkusza badawczego. Główny - `primary`, pomocniczy - `secondary`. Rola `stabilizer` jest dostępna, ale arkusz badawczy jej nie używa.

Każde ćwiczenie musi mieć co najmniej jeden mięsień `primary`.

### `exercise_equipment`

| Kolumna | Opis |
|---|---|
| `exercise` | `name_en` ćwiczenia |
| `equipment` | `name_en` sprzętu |

Sprzęt jest **wymagany łącznie (AND)**: ćwiczenie jest dostępne, gdy użytkownik ma wszystkie pozycje. Brak wierszy oznacza ćwiczenie bez sprzętu (masa ciała). Warianty „albo, albo” (np. sztanga lub suwnica Smitha) zapisuje się jako osobne ćwiczenia.

### `substitutes`

| Kolumna | Opis |
|---|---|
| `exercise` | ćwiczenie zastępowane |
| `substitute` | zamiennik |
| `priority_score` | im wyżej, tym lepszy zamiennik |

Relacja jest **kierunkowa**: A do B nie oznacza automatycznie B do A.

W arkuszu są 3 najlepsze zamienniki według wzoru:
```
priority_score = 10 × (wspólne mięśnie główne)
               +  1 × (wspólne mięśnie pomocnicze)
               +  1, jeśli zgodne is_compound
               +  1, jeśli zgodne is_unilateral
```

**TODO Do poprawy**

### `volumes`

| Kolumna | Opis |
|---|---|
| `muscle` | `code` mięśnia |
| `mev`, `mav_upper`, `mrv` | progi objętości (serie efektywne / tydzień) |
| `priority` | waga mięśnia w funkcji celu (0 = nie optymalizuj) |

Wartości pochodzą z arkusza `objetosc`, kolumny „(model)”: MEV = środek zakresu MEV, MAV górne = górna granica MAV, MRV = środek zakresu MRV.

**Na razie seed ich nie wczytuje.** Tabela progów per mięsień dojdzie w S2 razem z silnikiem. Do tego czasu konfiguracja `global-v1` używa progów globalnych równych medianom z tego arkusza: MEV 4, MAV 13, MRV 16.

## Konfiguracja modelu (tworzona przez seed, nie z arkusza)

`global-v1`, oznaczona jako domyślna. Wagi ról zgodnie z arkuszem `konfiguracja`:

| Rola | Waga (serie efektywne) |
|---|---|
| `primary` | 1.0 |
| `secondary` | 0.5 |
| `stabilizer` | 0.0 |

Seria w roli pomocniczej liczy się jako pół serii (fractional sets, Pelland i in. 2026). Pozostałe parametry mają wartości domyślne z modelu `ModelConfig`.

## Znane luki w katalogu

Brak ćwiczeń dla wzorców:
- `elbow_extension` (izolacja tricepsa),
- `calf_raise` (łydki; w katalogu nie ma też samego mięśnia),
- `knee_flexion` na maszynie (uginanie nóg).

Do uzupełnienia, gdy silnik pokaże niedobory objętości tych mięśni.

## Jak wprowadzać zmiany

1. Edytuj arkusz, korzystając z list rozwijanych.
2. `just seed`. Seed najpierw waliduje **cały** plik i wypisuje wszystkie błędy z numerami wierszy. Jeśli jakiś błąd wystąpi, nic nie zapisuje.
3. Seed jest idempotentny: można go uruchamiać wielokrotnie. Wiersze aktualizuje po kluczach, a dla każdego ćwiczenia z arkusza zastępuje cały zestaw relacji (role, sprzęt, zamienniki) tym z arkusza.
