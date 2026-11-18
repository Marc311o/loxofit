# Silnik Loxofit — model, ocena planu i optymalizacja

Ten dokument opisuje wszystko, co dzieje się między „plan treningowy” a „jedna liczba,
którą maksymalizuje generator”: z czego składa się model, jak liczona jest objętość,
korzyść i czas, jak tydzień bazowy rozwija się w mezocykl, jak działa szybki
ewaluator, przestrzeń przeszukiwania i algorytmy oraz jak je porównujemy.

Stan: konfiguracja domyślna `per-muscle-v2`, generator z minimum 2 seriami na ćwiczenie.

---

## Spis treści

1. [Mapa modułów](#1-mapa-modułów)
2. [Przepływ danych w skrócie](#2-przepływ-danych-w-skrócie)
3. [Dane wejściowe](#3-dane-wejściowe)
4. [Konfiguracje modelu i ich niezmienność](#4-konfiguracje-modelu-i-ich-niezmienność)
5. [Progresja: od tygodnia bazowego do mezocyklu](#5-progresja-od-tygodnia-bazowego-do-mezocyklu)
6. [Objętość: serie ułamkowe i limit na sesję](#6-objętość-serie-ułamkowe-i-limit-na-sesję)
7. [Funkcja korzyści i kara za MRV](#7-funkcja-korzyści-i-kara-za-mrv)
8. [Czas sesji](#8-czas-sesji)
9. [Funkcja celu](#9-funkcja-celu)
10. [Szybki ewaluator](#10-szybki-ewaluator)
11. [Przestrzeń przeszukiwania](#11-przestrzeń-przeszukiwania)
12. [Algorytmy optymalizacji](#12-algorytmy-optymalizacji)
13. [Porównanie algorytmów — protokół i wyniki](#13-porównanie-algorytmów--protokół-i-wyniki)
14. [Analiza planu w API](#14-analiza-planu-w-api)
15. [Założenia i ograniczenia modelu](#15-założenia-i-ograniczenia-modelu)
16. [Testy](#16-testy)
17. [Uruchamianie](#17-uruchamianie)
18. [Źródła](#18-źródła)

---

## 1. Mapa modułów

| Plik | Rola |
|---|---|
| `engine/types.py` | Typy wejściowe: `ExerciseSpec`, `MuscleTarget`, `EngineConfig`, `Session`, `Week`, `Mesocycle` |
| `engine/progression.py` | Tydzień bazowy → mezocykl (progresja serii, RIR, deload) |
| `engine/volume.py` | Objętość tygodniowa w seriach ułamkowych, objętość efektywna (limit na sesję) |
| `engine/benefit.py` | Funkcja korzyści `u(V)`, kara za przekroczenie MRV, wynik per mięsień |
| `engine/timing.py` | Czas serii, rozgrzewki, przerw i całej sesji; nadgodziny |
| `engine/evaluate.py` | **Implementacja referencyjna** funkcji celu (czytelna, na obiektach) |
| `engine/objective.py` | **Szybki ewaluator** — ta sama liczba, ~30× szybciej |
| `engine/focus.py` | Focus sesji (FBW / Upper / Lower / Push / Pull), szablony, pule ćwiczeń |
| `engine/space.py` | Przestrzeń przeszukiwania: reprezentacja, ograniczenia, naprawa, ruchy |
| `engine/optimizers/` | Losowe, zachłanne, hill climbing, algorytm genetyczny, memetyczny |
| `domains/plans/engine_adapter.py` | Baza danych → typy silnika, wynik silnika → schematy API |
| `scripts/config_versions.py` | Rejestr niezmiennych, wersjonowanych konfiguracji modelu |
| `scripts/seed_config.py` | Zapis rejestru do bazy, wykrywanie rozjazdów |
| `scripts/engine_eval.py` | CLI: ocena planu z pliku JSON bez serwera i bazy |
| `scripts/bench_objective.py` | Pomiar szybkości: referencja vs szybki ewaluator |

Silnik (`app/engine`) nie zna bazy danych ani FastAPI — to czysty Python bez
zależności. Wszystko, co dotyczy bazy, jest w adapterze i skryptach.

---

## 2. Przepływ danych w skrócie

```
katalog ćwiczeń ──► ExerciseSpec (role mięśni, tempo, compound, unilateral)
konfiguracja    ──► EngineConfig (wagi ról, krzywa, kary, czasy, progresja)
                ──► MuscleTarget per mięsień (MEV, MAV, MRV, priorytet)

tydzień bazowy (sesje × ćwiczenia × serie)
        │  progression.build_mesocycle
        ▼
mezocykl: T tygodni treningowych + 1 deload
        │  dla każdego tygodnia:
        │    volume  → V (cała objętość), E (efektywna, z limitem na sesję)
        │    benefit → priorytet · (u(E) − kara(V))   [tylko tygodnie treningowe]
        │    timing  → minuty sesji, nadgodziny        [wszystkie tygodnie]
        ▼
score = Σ korzyść − time_penalty · Σ nadgodziny
```

Generator przeszukuje **tylko tydzień bazowy** — resztę mezocyklu wyznacza
deterministyczna progresja. Każdy kandydat jest więc oceniany po rozwinięciu
w cały mezocykl.

---

## 3. Dane wejściowe

### 3.1. Ćwiczenie — `ExerciseSpec`

| Pole | Znaczenie |
|---|---|
| `code` | kod z katalogu, np. `bb_bench` |
| `is_compound` | wielostawowe (wpływa na zakres powtórzeń, przerwę, rozgrzewkę) |
| `muscle_roles` | mięsień → rola: `primary` / `secondary` / `stabilizer` |
| `tempo` | 4 znaki, np. `3010`; `None` → `default_tempo` z konfiguracji |
| `is_unilateral` | jednostronne — seria trwa dwa razy dłużej (dwie strony) |

Adapter (`build_spec`) bierze to z katalogu: role z tabeli `exercise_muscle_roles`,
tempo z `default_tempo` ćwiczenia.

### 3.2. Cel dla mięśnia — `MuscleTarget`

Tygodniowe progi objętości w seriach ułamkowych:

- **MEV** — minimalna objętość efektywna (poniżej niej brak wzrostu),
- **MAV_upper** — górna granica objętości maksymalnie adaptacyjnej,
- **MRV** — maksymalna objętość, z której da się zregenerować,
- **priority** — waga mięśnia w funkcji celu (0 = ignoruj).

Walidacja: `0 ≤ MEV < MAV_upper ≤ MRV`, `priority ≥ 0`.

Skąd się biorą (`engine_adapter.build_targets`):

- tryb **global** (`global-v1`): każdy mięsień z `is_volume_target = TRUE` dostaje te
  same progi z konfiguracji (4 / 13 / 16);
- tryb **per-muscle** (`per-muscle-v1`, `per-muscle-v2`): dokładnie mięśnie, dla których
  konfiguracja ma progi w tabeli `config_muscle_landmarks`. Mięsień bez progów nie
  jest oceniany.

Priorytet pochodzi z planu (`plan_muscle_targets`); brak wpisu = 1,0.

### 3.3. Plan — `Session`, `Week`, `Mesocycle`

- `Session`: uporządkowane ćwiczenia z liczbą serii + limit minut sesji
  (`max_minutes`). Kolejność ma znaczenie (rozgrzewki, ostatnia przerwa).
- `Week`: sesje, RIR tygodnia, flaga deloadu.
- `Mesocycle`: tygodnie; `training_weeks` = wszystkie poza deloadem.

---

## 4. Konfiguracje modelu i ich niezmienność

Wszystkie parametry modelu żyją w **wersjonowanych, niezmiennych konfiguracjach**
(`scripts/config_versions.py`). Plan zapisuje `config_id` w chwili utworzenia, więc
stary plan liczy się zawsze tak samo, nawet gdy model się rozwija. Zmiana modelu =
**nowa wersja**, nigdy edycja istniejącej.

Dodanie wersji:

1. dopisz `ConfigVersion` na końcu `CONFIGS` (nie usuwaj starych),
2. jeśli ma być domyślna — zmień `DEFAULT_CONFIG_NAME`,
3. uruchom `python -m app.scripts.seed_config`.

`seed_config` przed zapisem wykonuje `check_registry` (unikalne nazwy, znane
parametry, wagi dla wszystkich ról, progi tylko w konfiguracjach per-muscle i
uporządkowane), a po zapisie `config_drift` — jeśli wersja w bazie różni się od
kodu (parametry, wagi, progi), wypisuje ostrzeżenie.

Parametr, którego wersja nie podaje, bierze wartość domyślną kolumny. Nowe kolumny
dostają więc wartość domyślną odpowiadającą **dotychczasowemu** zachowaniu (limit
na sesję: `NULL`, przerwa przed kolejnym ćwiczeniem: `false`).

### 4.1. Wersje

| | `global-v1` | `per-muscle-v1` | `per-muscle-v2` (domyślna) |
|---|---|---|---|
| Progi | wspólne 4 / 13 / 16 | RP 2017 per mięsień | RP 2017 per mięsień |
| Limit serii na sesję | brak | 11 | 11 |
| Przerwa po ostatniej serii ćwiczenia | nie | nie | **tak** |
| Przejście między ćwiczeniami | 90 s | 90 s | **60 s** (samo stanowisko) |

### 4.2. Parametry wspólne (wartości domyślne `EngineConfig`)

| Grupa | Parametr | Wartość |
|---|---|---|
| Wagi ról | primary / secondary / stabilizer | 1,0 / 0,5 / 0,0 |
| Krzywa | `curve_k` | 3 |
| Kara MRV | `penalty_lambda` | 0,05 |
| Kara czasu | `time_penalty` | 0,1 / min |
| Przerwy | compound / izolacja | 150 s / 90 s |
| Rozgrzewka ogólna | `warmup_s` | 300 s |
| Serie rozgrzewkowe | `warmup_scheme` | 40%×8, 60%×5, 80%×3; przerwa 60 s |
| Tempo | `default_tempo`, faza X | `2010`, 1 s |
| Powtórzenia | compound / izolacja | 6–10 / 10–14 |
| Progresja | przyrost tygodniowy, maks. serii | +15%, 5 |
| RIR | start → koniec, deload | 3 → 1, 4 |
| Deload | mnożnik objętości | 0,5 |

### 4.3. Progi per mięsień (Israetel / Renaissance Periodization, 2017)

Tygodniowe serie: MEV / MAV_upper / MRV.

| Kod | Mięsień | MEV | MAV | MRV |
|---|---|---|---|---|
| `pec_major` | piersiowy większy | 10 | 20 | 22 |
| `lats` | najszerszy grzbietu | 10 | 22 | 25 |
| `trapezius` | czworoboczny | 0 | 20 | 26 |
| `delt_ant` | naramienny przedni | 0 | 8 | 12 |
| `delt_mid` | naramienny środkowy | 8 | 22 | 26 |
| `delt_post` | naramienny tylny | 8 | 22 | 26 |
| `biceps` | dwugłowy ramienia | 8 | 20 | 26 |
| `triceps` | trójgłowy ramienia | 6 | 14 | 18 |
| `quads` | czworogłowy uda | 8 | 18 | 20 |
| `bic_fem` | dwugłowy uda (hamstringi) | 6 | 16 | 20 |
| `glute_max` | pośladkowy wielki | 0 | 12 | 16 |
| `rect_abd` | prosty brzucha | 0 | 20 | 25 |

Nieoceniane (brak progów w źródle): skośne brzucha (`ext_obl`, `int_obl`),
prostowniki grzbietu (`erectors`). Naramienny środkowy i tylny mają w RP wspólny wpis.

Dwa zastrzeżenia (do opisania w pracy): RP to materiały praktyka, nie publikacja
recenzowana; RP liczy **serie bezpośrednie** i sam odlicza pracę pośrednią, a model
liczy **serie ułamkowe** — progi RP są tu przybliżeniem.

---

## 5. Progresja: od tygodnia bazowego do mezocyklu

`progression.build_mesocycle(base_week, weeks, config)` — mezocykl ma `weeks`
tygodni: `T = weeks − 1` treningowych i 1 deload (min. 2 tygodnie; w planie 2–12,
domyślnie 5).

Tydzień treningowy `w = 1..T`, ćwiczenie z `b` seriami w tygodniu bazowym:

```
sets_w = min( round_half_up(b · (1 + 0,15)^(w−1)),  max(b, max_sets_per_exercise) )
```

Deload:

```
sets = max(1, round_half_up(b · 0,5))
```

RIR maleje liniowo od `rir_start` do `rir_end` (zaokrąglenie w górę od połówki);
deload ma `deload_rir`.

Dla domyślnych parametrów i 5 tygodni (4 + deload):

| Seria bazowa | Tydz. 1 | 2 | 3 | 4 | Deload |
|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 2 | 1 |
| 2 | 2 | 2 | 3 | 3 | 1 |
| 3 | 3 | 3 | 4 | 5 | 2 |
| 4 | 4 | 5 | 5 | 5 | 2 |
| 5 | 5 | 5 | 5 | 5 | 3 |
| RIR | 3 | 2 | 2 | 1 | 4 |

Konsekwencje: przez zaokrąglanie czas sesji i objętość nie zmieniają się w każdym
tygodniu; ćwiczenie z 5 seriami bazowymi nie ma progresji (limit 5). Gdy użytkownik
ręcznie da więcej niż 5 serii, limitem jest jego wartość — serie nie spadają.

---

## 6. Objętość: serie ułamkowe i limit na sesję

### 6.1. Serie ułamkowe

Każda seria ćwiczenia dodaje każdemu mięśniowi `waga(rola)` serii:
primary 1,0, secondary 0,5, stabilizer 0 (pomijany).

Przykład: wyciskanie (`pec_major` primary, `delt_ant` i `triceps` secondary),
3 serie → klatka 3, przedni akton 1,5, triceps 1,5.

`V_m` — tygodniowa objętość mięśnia: suma po wszystkich sesjach tygodnia.

### 6.2. Objętość efektywna — limit na sesję

Powyżej pewnej liczby serii w jednej sesji kolejne serie nie dają już wzrostu
(Remmert i wsp., 2025 — preprint; ok. 11 serii ułamkowych). Dlatego:

```
E_m = Σ_sesje min(V_m,sesja, cap)          cap = 11 (per-muscle-v1/v2), brak w global-v1
```

- **E** (efektywna) liczy się do **korzyści**,
- **V** (cała) liczy się do **kary MRV** — serie ponad limit nadal męczą.

Przykład: jedna sesja z wyciskaniem 6 + wyciskaniem wąsko 6 → klatka V = 12,
E = 11. Te same serie rozłożone na dwie sesje → V = E = 12. Model nagradza więc
rozkładanie objętości mięśnia na kilka sesji.

---

## 7. Funkcja korzyści i kara za MRV

Dla mięśnia z progami MEV, MAV_upper, MRV i stałej `k = curve_k`:

```
τ = (MAV_upper − MEV) / k

u(E) = 1 − exp(−(E − MEV) / τ)      dla E ≥ MEV   (malejące przyrosty)
u(E) = (E − MEV) / τ                dla E < MEV   (styczna w MEV — liniowo ujemna)

kara(V) = λ · max(0, V − MRV)²

score_m = priority_m · ( u(E_m) − kara(V_m) )
```

Własności:

- `u(MEV) = 0`; `u(MAV_upper) = 1 − e^(−k) ≈ 0,950` dla `k = 3` — przy górnej
  granicy MAV mięsień ma 95% możliwej korzyści; dalej przyrosty są znikome;
- poniżej MEV funkcja jest ciągła i ma ciągłą pochodną (nachylenie `1/τ` z obu
  stron) — kara za niedobór rośnie liniowo, przy MEV = 10 i V = 0 wynosi −3;
- mięśnie z MEV = 0 (czworoboczny, pośladki, przedni akton, brzuch) nie mają
  obszaru ujemnego;
- kara MRV jest kwadratowa: 2 serie ponad → 0,2, 4 serie → 0,8.

Przykład — klatka (10 / 20 / 22), τ = 3,33, przy E = V:

| V | 0 | 5 | 10 | 12 | 15 | 20 | 22 | 24 | 26 |
|---|---|---|---|---|---|---|---|---|---|
| u | −3,00 | −1,50 | 0 | 0,45 | 0,78 | 0,95 | 0,97 | 0,99 | 0,99 |
| kara | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0,20 | 0,80 |
| score | −3,00 | −1,50 | 0 | 0,45 | 0,78 | 0,95 | 0,97 | 0,79 | 0,19 |

Mięśnie bez celu są ignorowane; mięsień z celem, ale bez objętości, ma V = 0.

---

## 8. Czas sesji

### 8.1. Seria robocza

```
czas_powtórzenia = suma 4 faz tempa: ekscentryczna, pauza dół, koncentryczna, pauza góra
                   cyfra = sekundy; „X” lub „0” w fazie ruchu = 1 s (explosive_phase_s);
                   „X” w pauzie jest błędem
powtórzenia      = środek zakresu: compound (6+10)//2 = 8, izolacja (10+14)//2 = 12
czas_serii       = powtórzenia × czas_powtórzenia × (2 jeśli jednostronne)
```

Przykład: tempo `3010` = 4 s/powt.; wyciskanie 8 × 4 = 32 s. Izolacja z tempem
domyślnym `2010` = 3 s/powt. → 12 × 3 = 36 s.

### 8.2. Rozgrzewka

- ogólna: 300 s na sesję,
- serie rozgrzewkowe (40%×8, 60%×5, 80%×3 — procenty nie wpływają na czas,
  liczą się powtórzenia), każda z przerwą 60 s — **tylko** dla ćwiczenia
  wielostawowego, którego mięśnie główne nie były jeszcze trenowane przez
  wcześniejsze ćwiczenie wielostawowe w tej sesji.

Izolacja przed ćwiczeniem wielostawowym nie zwalnia go z rozgrzewki (prostowanie
nóg nie zastępuje rozgrzewki przysiadu), więc model nie nagradza czasem kolejności
„najpierw izolacja”.

Przykład: wyciskanie (`3010`): 16 powt. × 4 s + 3 × 60 s = 244 s.

### 8.3. Przerwy i przejścia (`per-muscle-v2`)

- przerwa po **każdej** serii roboczej (compound 150 s, izolacja 90 s),
  **oprócz ostatniej serii sesji** — po niej nic już nie następuje;
- przejście między ćwiczeniami: 60 s na przygotowanie stanowiska.

```
t_sesji = warmup_s
        + Σ_ćwiczenia [ serie_i · czas_serii_i  +  serie_i · przerwa_i  +  rozgrzewka_i ]
        − przerwa_ostatniego_ćwiczenia
        + (liczba_ćwiczeń − 1) · transitions_s
```

W starym modelu (`global-v1`, `per-muscle-v1`) przerw było `serie − 1` na każde
ćwiczenie, a przejście trwało 90 s. To powodowało artefakt: dodatkowa seria
izolacji kosztowała 36 + 90 = 126 s, a nowe ćwiczenie z 1 serią też 36 + 90 = 126 s
(dla wielostawowych nowe ćwiczenie było wręcz tańsze), więc optymalizator
rozbijał serie na wiele ćwiczeń po 1 serii. W v2 nowe ćwiczenie kosztuje
90 (przerwa) + 60 (stanowisko) + 36 = 186 s.

### 8.4. Przykład

Sesja: wyciskanie 3 serie, pec deck 2 serie.

| Składnik | v1 | v2 |
|---|---|---|
| rozgrzewka ogólna | 300 | 300 |
| wyciskanie: 3 × 32 | 96 | 96 |
| przerwy wyciskania | 2 × 150 = 300 | 3 × 150 = 450 |
| rozgrzewka wyciskania | 244 | 244 |
| przejście | 90 | 60 |
| pec deck: 2 × 36 + 1 przerwa (ostatnie ćwiczenie) | 162 | 162 |
| **Razem** | **1192 s = 19,9 min** | **1312 s = 21,9 min** |

### 8.5. Nadgodziny

```
nadgodziny_sesji = max(0, t_sesji / 60 − max_minutes)
```

liczone **w każdym tygodniu mezocyklu, także w deloadzie** — liczba serii rośnie z
tygodniem, więc plan mieszczący się w limicie w tygodniu 1 może go przekraczać w
tygodniu 4.

---

## 9. Funkcja celu

```
score =   Σ_{w=1..T}  Σ_{m: p_m > 0}  p_m · ( u_m(E_{m,w}) − λ · max(0, V_{m,w} − MRV_m)² )
        − c · Σ_{w=1..T+1}  Σ_s  max(0, t_{s,w} / 60 − L_s)
```

- `T` — tygodnie treningowe (deload nie liczy się do korzyści),
- `c = time_penalty` = 0,1 za minutę,
- `L_s` — limit minut sesji `s`.

Skala: jeden mięsień w jednym tygodniu przy MAV daje ≈ 0,95; 10 minut ponad limit w
jednej sesji jednego tygodnia kosztuje 1,0 — mniej więcej tyle samo.

### 9.1. Maksimum i procent maksimum

```
max_score = Σ_m p_m · (1 − e^(−k)) · T
```

czyli każdy mięsień na górnej granicy MAV w każdym tygodniu treningowym, bez kary
czasu. Dla 12 mięśni RP z priorytetem 1 i 4 tygodni: 12 · 0,950 · 4 = **45,6**.

To górne ograniczenie, a nie osiągalny cel: suma MAV z RP to ok. 200 serii
ułamkowych tygodniowo, czego nie da się zmieścić w typowych limitach czasu.
Procent maksimum jest więc miarą porównawczą (między planami i algorytmami przy tych
samych ograniczeniach), a nie oceną „jak dobry jest plan”.

`score` może być ujemny (mięśnie poniżej MEV, nadgodziny).

---

## 10. Szybki ewaluator

### 10.1. Po co

Implementacja referencyjna (`evaluate.evaluate_plan`) dla każdego kandydata buduje
cały mezocykl z obiektów i liczy od nowa rzeczy, które się nie zmieniają.
Optymalizator ocenia dziesiątki tysięcy kandydatów na tym samym katalogu, więc
`objective.Objective` liczy je raz:

- **per ćwiczenie**: wagi objętości dla ocenianych mięśni, czas serii roboczej,
  przerwa po serii, czas rozgrzewki, mięśnie główne jako maska bitowa;
- **per liczba serii bazowych**: serie w każdym tygodniu (progresja + deload);
- **per gen (ćwiczenie, serie bazowe)**: objętość i sekundy w każdym tygodniu —
  w pamięci podręcznej przy pierwszym użyciu.

Ocena kandydata to wtedy tylko dodawanie, limit na sesję, nadgodziny i funkcja
korzyści.

### 10.2. Wynik

Na syntetycznym problemie (45 ćwiczeń, 14 mięśni, 4 sesje × 6 ćwiczeń, 5 tygodni):

| | czas na kandydata |
|---|---|
| referencja | 1,74 ms |
| szybki ewaluator | 58 µs (~30×) |

Czysty Python, bez numpy.

### 10.3. Gwarancja równoważności

`tests/engine/test_objective.py` porównuje oba wyniki na **300 losowych
problemach × 5 kandydatów**: losowe ćwiczenia (1–12, role, tempa, jednostronne),
losowe progi i priorytety, losowa konfiguracja (wagi ról, `k`, `λ`, kara czasu,
limit na sesję: brak / 4 / 11, **oba modele czasu**, przejście 30/60/90 s, przyrost,
maks. serii), 2–8 tygodni, 1–6 sesji z limitami, puste sesje. Tolerancja 1e-9.
Każda zmiana modelu musi trafić do obu implementacji — test to wychwyci.

---

## 11. Przestrzeń przeszukiwania

### 11.1. Co jest decyzją, a co daną

| Ustala użytkownik | Wybiera algorytm |
|---|---|
| liczba sesji, ich focus (szablon albo custom), limity minut | ćwiczenia w każdej sesji |
| długość mezocyklu, priorytety mięśni, sprzęt | liczba serii bazowych każdego ćwiczenia |

**Kolejność ćwiczeń w sesji nie jest przeszukiwana.** Sesja jest zawsze
posortowana według `rank`: najpierw wielostawowe, potem trudniejsze technicznie
(`complexity` malejąco), potem bardziej męczące (`fatigue_cost` malejąco) — tak samo
jak rekomendowana kolejność w edytorze. Zmniejsza to przestrzeń i daje czytelne
plany. Kolejność wpływa na czas tylko przez rozgrzewki i ostatnią przerwę.

### 11.2. Reprezentacja

```
gen        = (indeks ćwiczenia, serie bazowe)
sesja      = krotka genów, posortowana według rank
kandydat   = krotka sesji
```

Kandydaci są niezmienni — ruch tworzy nowego kandydata i kopiuje tylko zmienioną
sesję.

### 11.3. Focus i pule ćwiczeń (`focus.py`)

Ćwiczenie pasuje do sesji, gdy **wszystkie jego mięśnie główne** należą do focusu
sesji. Mięśnie pomocnicze mogą wychodzić poza focus (wiosłowanie pracuje bicepsem
w dniu pleców). Mięśnie brzucha pasują do każdego focusu.

| Focus | Dozwolone mięśnie główne |
|---|---|
| Full body | dowolne |
| Upper | Push ∪ Pull ∪ Core |
| Lower | czworogłowy, dwugłowy uda, pośladkowy, prostowniki ∪ Core |
| Push | piersiowy, naramienny przedni i środkowy, triceps ∪ Core |
| Pull | najszerszy, czworoboczny, naramienny tylny, biceps ∪ Core |

Core = prosty brzucha, skośne zewnętrzne i wewnętrzne.

Szablony powtarzają cykl: FBW → F, F, F…; Upper/Lower → U, L, U, L…;
PPL → Push, Pull, Lower, Push… Opcja custom pozwala dać każdej sesji własny focus.

Pule na pełnym katalogu (45 ćwiczeń): Full body 45, Upper 25, Lower 22, Push 14,
Pull 13. Pule zawęża też sprzęt użytkownika (domena generatora).

### 11.4. Ograniczenia

- ćwiczenie tylko z puli sesji, bez powtórzeń w sesji (to samo ćwiczenie może
  być w kilku sesjach),
- serie bazowe 2–5 (`min_sets = 2` — pojedyncza seria rzadko jest warta
  przygotowania stanowiska i rozgrzewki; w edytorze użytkownik może dać 1),
- 1–8 ćwiczeń na sesję.

Rozmiar przestrzeni dla jednej sesji (do 8 z `n` ćwiczeń, 4 warianty serii):
n = 13 → ~10⁸, n = 22 → ~2·10¹⁰, n = 45 → ~10¹³. Cały plan Upper/Lower 4× to
rzędu 10⁴², FBW 3× — 10³⁹. Pełne przeszukanie jest wykluczone.

`repair` naprawia dowolnego kandydata (po krzyżowaniu): usuwa ćwiczenia spoza puli
i duplikaty, przycina serie do zakresu i sesję do 8 ćwiczeń, pustej sesji daje
najwyżej sklasyfikowane ćwiczenie z puli z minimalną liczbą serii.

### 11.5. Ruchy (sąsiedztwo)

| Ruch | Waga | Działanie |
|---|---|---|
| `sets` | 0,35 | ±1 seria jednego ćwiczenia |
| `swap` | 0,30 | zamiana ćwiczenia na inne z puli; w 80% przypadków na ćwiczenie dzielące mięsień główny („podobne”) |
| `add` | 0,15 | nowe ćwiczenie z losową liczbą serii |
| `remove` | 0,10 | usunięcie ćwiczenia (sesja nie może zostać pusta) |
| `move` | 0,10 | przeniesienie ćwiczenia do innej sesji (jeśli pasuje do jej puli) |

Ruch, który nie ma zastosowania (np. `add` w pełnej sesji), jest zastępowany innym
z pozostałych. Te same ruchy służą jako sąsiedztwo hill climbingu i mutacja GA —
dzięki temu porównanie algorytmów jest uczciwe.

---

## 12. Algorytmy optymalizacji

### 12.1. Wspólny interfejs

```python
f(objective, space, budget, rng, on_progress=None, ...) -> SearchResult
```

- **budżet w liczbie ocen**, nie w sekundach — wynik nie zależy od maszyny, każdy
  algorytm dostaje tyle samo pracy;
- `Evaluator` liczy oceny, pamięta najlepszego kandydata i historię poprawy
  (`(ocena nr, wynik)` przy każdej poprawie), co 500 ocen raportuje postęp; po
  wyczerpaniu budżetu rzuca `BudgetExhausted`, co kończy przeszukiwanie;
- ten sam seed → ten sam wynik.

### 12.2. Losowe przeszukiwanie (punkt odniesienia)

Losowi kandydaci do końca budżetu, najlepszy wygrywa.

### 12.3. Zachłanny (punkt odniesienia)

Start z pustego planu. W każdym kroku ocenia wszystkie zmiany „dodaj ćwiczenie z
minimalną liczbą serii do sesji” i „+1 seria istniejącego ćwiczenia” i bierze
najlepszą. Kończy, gdy żadna zmiana nie poprawia wyniku (optimum lokalne).
Deterministyczny. Sesja pozostawiona pusta dostaje naprawę; tę końcową ocenę
liczymy poza budżetem.

### 12.4. Hill climbing z restartami

Z losowego kandydata: jeden losowy ruch, przyjęty, jeśli nie jest gorszy
(równe przyjmujemy, żeby przechodzić płaskowyże). Po 500 ruchach bez poprawy —
restart z nowego losowego kandydata.

### 12.5. Algorytm genetyczny

| Parametr | Wartość |
|---|---|
| populacja | 60 |
| selekcja | turniejowa, k = 3 |
| elityzm | 2 |
| krzyżowanie | prawdopodobieństwo 0,9 |
| mutacja | ruch z prawdopodobieństwem 0,6, powtarzany z tym samym prawdopodobieństwem (średnio 1,5 ruchu) |

Krzyżowanie:

- **session** (domyślne): każda sesja w całości od jednego z rodziców — zachowuje
  sesje, które dobrze ze sobą działają;
- **gene**: w każdej sesji każde ćwiczenie któregoś z rodziców trafia do dziecka z
  prawdopodobieństwem 1/2, potem naprawa.

Przy 30 000 ocen to ok. 500 pokoleń.

### 12.6. Wariant memetyczny

GA + lokalne przeszukiwanie: po zbudowaniu każdego pokolenia 2 najlepsze osobniki
dostają do 25 kroków hill climbingu (z tego samego budżetu). Pokolenie kosztuje
wtedy 58 + 50 ocen, więc ok. 46% budżetu idzie na lokalne dopracowanie; przy
30 000 ocen to ok. 280 pokoleń.

---

## 13. Porównanie algorytmów — protokół i wyniki

### 13.1. Protokół (wstępny)

- katalog: pełny (45 ćwiczeń), cały sprzęt, progi RP, priorytety 1,
- konfiguracja `per-muscle-v2`, serie 2–5, maks. 8 ćwiczeń, mezocykl 5 tygodni,
- budżet 30 000 ocen, 5 seedów na algorytm,
- miara: średni wynik i procent maksimum (45,6), odchylenie, najlepszy.

| Scenariusz | Losowe | Zachłanny | Hill climbing | GA | Memetyczny |
|---|---|---|---|---|---|
| Upper/Lower 4 × 60 min | 39,9% | 54,7% | **70,9%** | 69,6% | 69,5% |
| FBW 3 × 60 min | 25,6% | 35,4% | **56,5%** | 54,8% | 55,1% |
| PPL 3 × 45 min | 6,0% | 10,5% | **24,5%** | **24,5%** | 24,1% |

Czas jednego przebiegu: ok. 2–3 s.

### 13.2. Obserwacje

- trzy metody przeszukiwania lokalnego/populacyjnego są blisko siebie; hill
  climbing minimalnie najlepszy, GA ma większy rozrzut między seedami;
- zachłanny zatrzymuje się wcześnie — dodanie ćwiczenia z 2 seriami często od razu
  się nie opłaca (czas), więc trafia w płytkie optimum lokalne;
- PPL 3 × 45 min jest bardzo ciasny czasowo — stąd niskie procenty;
- plany v2 mają 3–5 ćwiczeń na sesję, zwykle po 4–5 serii (artefakt 1-seryjnych
  ćwiczeń zniknął).

### 13.3. Do zrobienia (strojenie, #34)

- więcej seedów (30) i scenariuszy, test istotności różnic,
- strojenie parametrów GA i memetycznego (populacja, mutacja, liczba i długość
  lokalnych przeszukiwań), patience hill climbingu,
- krzywe zbieżności (historia z `SearchResult`),
- sprawdzenie zjawisk widocznych w wynikach: dużo ćwiczeń z maksymalną liczbą
  serii (brak progresji przy 5), kilka wariantów martwego ciągu w jednej sesji,
  czworogłowe trenowane głównie izolacją.

---

## 14. Analiza planu w API

`GET /plans/{id}/analysis` (`PlanService.analyze`):

- jeśli plan ma wszystkie tygodnie zapisane (po wygenerowaniu progresji) — ocenia
  **zapisane** tygodnie (`source = stored`), z ręcznymi zmianami użytkownika;
- w przeciwnym razie rozwija tydzień bazowy progresją (`source = projected`).

Ocena idzie przez implementację referencyjną (`evaluate`), z konfiguracją, z którą
plan został utworzony. Odpowiedź (`to_analysis`):

- `score`, `max_score`, `volume_score`, `time_penalty`,
- `assumptions`: zakresy powtórzeń, tempo domyślne, limit serii na sesję,
- per tydzień: RIR, deload, wynik objętości, minuty sesji, nadgodziny,
- per mięsień: `volume` (V), `effective_volume` (E), strefa (`below_mev`,
  `mev_mav`, `mav_mrv`, `above_mrv` — według V), progi, priorytet, korzyść,
  kara, wynik (dla deloadu: brak).

Frontend (`features/plan`) buduje na tym paski objętości, legendę progów i listę
problemów (np. mięsień poniżej MEV, ponad MRV, sesja ponad limit, serie ucięte
limitem na sesję).

---

## 15. Założenia i ograniczenia modelu

Do rozdziału 4 pracy.

**Objętość i korzyść**

1. Objętość mierzona w seriach ułamkowych (primary 1, secondary 0,5, stabilizer 0).
2. Progi per mięsień z RP 2017 — przybliżenie (serie bezpośrednie vs ułamkowe).
3. Mięśnie bez progów w źródle nie są oceniane.
4. Korzyść wykładnicza z nasyceniem w MAV (k = 3 → 95% w MAV_upper), liniowo
   ujemna poniżej MEV, kwadratowa kara ponad MRV.
5. Limit 11 serii na mięsień w sesji (preprint, Remmert 2025): powyżej korzyść
   się nie zwiększa, zmęczenie (MRV) tak.
6. Wszystkie serie robocze traktowane jako równie bodźcowe; RIR nie wpływa na
   korzyść.
7. Ciężar nie jest modelowany.

**Czas**

8. Liczba powtórzeń do szacowania czasu = środek zakresu.
9. Czas powtórzenia z tempa; faza wybuchowa = 1 s.
10. Stałe przerwy: 150 s (wielostawowe), 90 s (izolacja), także po ostatniej
    serii ćwiczenia (v2); 60 s na przygotowanie stanowiska.
11. Serie rozgrzewkowe tylko dla wielostawowego, którego mięśnie główne nie były
    rozgrzane wcześniejszym wielostawowym.

**Mezocykl**

12. Progresja +15% serii tygodniowo, maks. 5 serii, deload 50% w ostatnim tygodniu.
13. Deload nie liczy się do korzyści, ale liczy się do czasu.

**Generator**

14. Kolejność ćwiczeń ustalona regułą (rank), nie optymalizowana.
15. Focus sesji ustalany przez mięśnie główne; brzuch dozwolony wszędzie.
16. Minimum 2 serie na ćwiczenie w proponowanym planie.
17. Procent maksimum to miara porównawcza, nie bezwzględna jakość.

---

## 16. Testy

| Plik | Co sprawdza |
|---|---|
| `tests/engine/test_timing.py` | tempo, czas serii, rozgrzewki, przykłady liczbowe obu modeli czasu, dodatkowe ćwiczenie droższe niż dodatkowa seria |
| `tests/engine/test_volume.py` | serie ułamkowe, limit na sesję |
| `tests/engine/test_benefit.py` | kształt `u(V)`, kara MRV, priorytety |
| `tests/engine/test_progression.py` | progresja, RIR, deload |
| `tests/engine/test_evaluate.py` | funkcja celu na całych planach |
| `tests/engine/test_objective.py` | równoważność szybkiego ewaluatora z referencją (300 × 5) |
| `tests/engine/test_focus.py` | focus, szablony, pule |
| `tests/engine/test_space.py` | ważność losowych kandydatów, ruchów i naprawy; min. 2 serie; preferencja podobnych ćwiczeń |
| `tests/engine/test_optimizers.py` | budżet, ważność wyniku, powtarzalność, monotoniczna historia, wszystkie metody znajdują optimum małego problemu sprawdzonego pełnym przeszukaniem |
| `tests/scripts/test_engine_eval.py` | rejestr konfiguracji, mapowanie progów i wag, konfiguracja domyślna |
| `tests/domains/plans/test_plans.py` | analiza w API, tryb per-muscle, założenia |

---

## 17. Uruchamianie

```bash
cd backend

# testy
python -m pytest -q
python -m pytest tests/engine -q          # sam silnik, bez bazy

# ocena planu z pliku (bez serwera i bazy)
python -m app.scripts.engine_eval data/plans/example_upper_lower.json
python -m app.scripts.engine_eval PLAN --config global-v1 --weeks 6 --json

# szybkość: referencja vs szybki ewaluator
python -m scripts.bench_objective

# konfiguracje do bazy (po migracjach i seedzie katalogu)
python -m app.scripts.seed_config
```

Plik planu dla `engine_eval`:

```json
{
  "weeks": 5,
  "sessions": [
    {"name": "Upper A", "max_minutes": 60,
     "exercises": [{"exercise": "bb_bench", "sets": 3}]}
  ]
}
```

---

## 18. Źródła

- Israetel M. (2017). *Training Volume Landmarks for Muscle Growth*. Renaissance
  Periodization. https://rpstrength.com/training-volume-landmarks-muscle-growth/
- Remmert J. i wsp. (2025). *Is There Too Much of a Good Thing?* SportRxiv,
  preprint. https://sportrxiv.org/index.php/server/preprint/view/537