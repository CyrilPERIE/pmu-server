# Audit code — epmu/server v1.0

**Date** : 8 août 2026  
**Périmètre** : code source Python du projet (hors `.venv`, `.git`)  
**Objectif** : identifier les incohérences structurelles, le code dupliqué, les imports inutilisés, et les axes d'amélioration de robustesse.

> **Exemples détaillés avant/après** : voir la **section 12** (annexe complète avec code réel du projet et propositions concrètes).  
> **Parallélisme HTTP et pipelines** : voir les **sections 13 et 14**.

---

## 1. Vue d'ensemble

### 1.1 Rôle du projet

Application FastAPI qui :

- interroge l'API PMU (courses hippiques) ;
- persiste les réponses brutes en PostgreSQL (JSON via SQLModel) ;
- exécute des pipelines de scraping planifiés (toutes les 5 minutes + quotidien à 4h).

### 1.2 Stack technique

| Couche        | Technologie                                       |
| ------------- | ------------------------------------------------- |
| HTTP          | FastAPI, Uvicorn                                  |
| ORM           | SQLModel / SQLAlchemy 2                           |
| Migrations    | Alembic                                           |
| Client PMU    | `requests` (synchrone)                            |
| Planification | `fastapi-utilities` (`repeat_every`, `repeat_at`) |
| Config        | `python-dotenv` (`DATABASE_URL`)                  |

### 1.3 Architecture actuelle (implicite)

```
server.py
  ├── api/routes/          → endpoints HTTP
  ├── service/             → accès DB (CRUD)
  ├── scraper/
  │     ├── orchestrator   → planification
  │     └── pipelines/     → logique de scraping
  ├── pmu/                 → client API externe
  ├── models/              → schémas SQLModel
  └── utils/               → logging
```

**Points positifs** : séparation en couches lisible, modèles homogènes (`id` + `raw` JSON), migrations Alembic en place.

**Niveau de maturité** : prototype avancé, pas encore production-ready (bugs runtime, zéro test, gestion d'erreurs minimale).

---

## 2. Incohérences de structure et d'architecture

### 2.1 Couche API sans injection de dépendances

Les routes ouvrent manuellement des sessions DB via `with get_session() as session:` au lieu d'utiliser `Depends(get_db)`. Aucun schéma Pydantic de réponse n'est défini.

Conséquence : logique métier et accès DB dispersés, difficile à tester et à factoriser.

**Fichiers concernés** : `api/routes/scrap.py`, `api/routes/metrics.py`, tous les pipelines.

→ **Exemple complet** : §12.1 (session DB + `Depends`)

### 2.2 Routes `async` avec code 100 % synchrone bloquant

```python
# api/routes/scrap.py — route async, exécution synchrone longue
@router.get("/historize")
async def historize(...):
    historize(start_date=start, end_date=end)  # bloque l'event loop
```

Idem pour `server.py` route `/` qui appelle `scrap_programmes()` de façon synchrone.

**Impact** : sous charge, l'event loop FastAPI est bloquée ; les autres requêtes attendent.

**Recommandation** : soit retirer `async` et déclarer les routes sync, soit déléguer à `BackgroundTasks` / worker externe.

→ **Exemple complet** : §12.2 (route historize + BackgroundTasks), §12.14 (route `/`)

### 2.3 Duplication métriques : `service/metrics.py` vs `service/course.py` vs route

- `api/routes/metrics.py` appelle correctement `count_courses`, `count_active_courses`, etc. dans `service/course.py` et `service/rapport.py`.
- `service/metrics.py` existe mais est **incomplet, cassé, et jamais importé**.

Incohérence : deux endroits pour la même responsabilité, dont un mort.

### 2.4 Planification dupliquée au démarrage

Dans `server.py` :

```python
@app.on_event('startup')
def startup_event():
    setup_logging()
    every_day()           # exécution immédiate
    every_five_minutes()  # exécution immédiate

@app.on_event('startup')
@repeat_every(seconds=60 * 5)
def every_five_minutes_task(): ...

@app.on_event('startup')
@repeat_at(cron='0 4 * * *')
def every_day_task(): ...
```

Au boot : scraping complet **immédiat** + tâches cron planifiées → risque de surcharge et de double exécution.

→ **Exemple complet** : §12.13 (timeline au boot + schéma worker séparé)

### 2.5 `@app.on_event('startup')` déprécié

FastAPI recommande le pattern `lifespan`. Trois handlers `startup` séparés compliquent le cycle de vie de l'application.

### 2.6 Absence de couche repository

Chaque entité (`course`, `programme`, `rapport`, etc.) répète le même pattern :

```python
def create_X(x_create: XCreate, session: Session) -> X:
    x = X.model_validate(x_create)
    session.merge(x)
    session.commit()
    return x
```

Les pipelines ouvrent **une session + un commit par enregistrement** :

```python
# scraper/pipelines/scrap_courses.py
for course in courses:
    with get_session() as session:
        create_course(CourseCreate(...), session)  # commit à chaque itération
```

**Impact** : performance dégradée, transactions atomiques impossibles sur un batch.

→ **Exemple complet** : §12.6 (1 commit par programme vs 88 commits)

### 2.7 Modèle « document store » sans relations SQL

Toutes les tables = `id: str` + `raw: JSON` (+ flags `is_over`, `is_scraped`). Pas de FK, pas de relations SQLAlchemy.

C'est cohérent pour du scraping brut, mais :

- pas de contraintes d'intégrité référentielle ;
- logique métier basée sur parsing d'IDs string (`"08082026/R1/C3"`) ;
- jointures analytiques impossibles en SQL.

### 2.8 Types Pydantic PMU déclarés mais non utilisés

`pmu/endpoints.py` annote les retours (`Course`, `ProgrammeResponse`, etc.) mais retourne le `dict` brut :

```python
def get_course(course_identifier: CourseIdentifier) -> Course | None:
    response = fetch_pmu_api(str(course_identifier))
    return response  # dict, pas un modèle Pydantic validé
```

Les pipelines accèdent ensuite en notation dict : `programme['programme']['reunions']`.

**Incohérence** : annotations mensongères, pas de validation à l'entrée.

→ **Exemple complet** : §12.11 (validation Pydantic `model_validate`)

### 2.9 Double `__init__` sur `CourseIdentifier` (dead code)

```python
# pmu/types/types.py
class CourseIdentifier:
    def __init__(self, course_num: int, reunion_num: int, programme: str): ...
    def __init__(self, course_id: str):  # écrase le précédent — seul celui-ci est actif
```

Le constructeur `(int, int, str)` est du code mort.

→ **Exemple complet** : §12.15

### 2.10 Dates minimales incohérentes

| Fichier                          | Constante     | Valeur                         |
| -------------------------------- | ------------- | ------------------------------ |
| `scraper/pipelines/historize.py` | `LOWEST_DATE` | `"01012014"`                   |
| `pmu/client.py`                  | `MIN_DATE`    | `"01012016"` (jamais utilisée) |

### 2.11 Endpoints PMU morts

Fonctions définies dans `pmu/endpoints.py` mais jamais appelées :

- `get_reunion`
- `get_pronostics`
- `get_pronostics_détaillés`
- `get_rapport_par_bet_type`
- `get_rapports_definitifs_par_bet_type`

### 2.12 Fonctions service mortes

| Fichier                | Fonctions non utilisées                                                      |
| ---------------------- | ---------------------------------------------------------------------------- |
| `service/course.py`    | `get_courses`, `get_daily_courses`                                           |
| `service/programme.py` | `get_programme_by_identifier`, `get_programmes`, `get_programme_identifiers` |

### 2.13 Fichiers `__init__.py` absents

Pas de `api/__init__.py`, `service/__init__.py`, `scraper/__init__.py`. Les imports fonctionnent via namespace packages (PEP 420) si lancé depuis la racine, mais c'est fragile selon le contexte d'exécution.

### 2.14 Naming et langue

| Élément                        | Problème                                         |
| ------------------------------ | ------------------------------------------------ |
| `scrap_*`                      | Anglais approximatif (« scrape » serait correct) |
| `get_pronostics_détaillés`     | Accent dans un identifiant Python                |
| Migration `increase_id_lenght` | Typo : « lenght » → « length »                   |
| Commentaires FR + code EN      | Mélange systématique                             |

---

## 3. Code mutualisable

### 3.1 Pattern `create_*` — 6 occurrences identiques

Fichiers : `service/course.py`, `programme.py`, `rapport.py`, `combinaison.py`, `participant.py`, `reunion.py`.

```python
def create_X(x_create: XCreate, session: Session) -> X:
    x = X.model_validate(x_create)
    session.merge(x)
    session.commit()
    return x
```

**Proposition** : helper générique ou classe `Repository[T]` :

→ **Exemple complet** : §12.7 (3 variantes : helper, repository, commit optionnel)

### 3.2 Squelette des pipelines scraper

Structure commune à `scrap_courses`, `scrap_participants`, `scrap_bet`, `scrap_programmes` :

1. `logger.info(...)`
2. `with get_session()` → récupérer les IDs actifs / non scrapés
3. Boucle sur chaque élément
4. Appel API PMU
5. `with get_session()` → `create_*`

**Proposition** : fonction générique ou classe de pipeline avec session unique par batch :

```python
def scrap_batch(session, items, fetch_fn, persist_fn):
    for item in items:
        data = fetch_fn(item)
        if data is None:
            continue
        persist_fn(session, item, data)
    session.commit()
```

### 3.3 Validation de dates programme

Logique dupliquée entre :

- `api/routes/scrap.py` (L17-20) : validation manuelle `isdigit()` + `len == 8`
- `historize.py` : bornes `LOWEST_DATE` / `HIGHEST_DATE`

**Proposition** : extracteur `parse_programme_date(s: str) -> ProgrammeIdentifier | HTTPException`.

→ **Exemple complet** : §12.3

### 3.4 Comptage métriques

`service/course.py` expose déjà `count_courses`, `count_active_courses`, `count_inactive_courses`. La route metrics les appelle directement — c'est correct. Supprimer `service/metrics.py` et centraliser éventuellement dans une seule fonction `get_all_metrics(session)`.

### 3.5 Client HTTP PMU

Centraliser dans `fetch_pmu_api` :

- retry avec backoff ;
- timeout ;
- gestion des codes HTTP non-200 (au lieu de `return None` au premier échec).

→ **Exemple complet** : §12.4 (retry + timeout + backoff)

### 3.6 `scrap_programmes` vs `scrap_past_programmes`

Deux fonctions très proches (fetch programme → `create_programme`). Factorisable en une seule avec paramètre `programme_identifier`.

→ **Exemple complet** : §12.17

---

## 4. Imports inutilisés et code mort

Analyse statique (ruff F401/F841) + revue manuelle.

### 4.1 Imports inutilisés confirmés

| Fichier                                      | Import inutilisé                               |
| -------------------------------------------- | ---------------------------------------------- |
| `server.py`                                  | `ProgrammeIdentifier`                          |
| `server.py`                                  | `historize` (pipeline)                         |
| `scraper/pipelines/scrap_past_programmes.py` | `date`                                         |
| `scraper/pipelines/scrap_past_programmes.py` | `date_to_programme_date`                       |
| `pmu/client.py`                              | `MIN_DATE` (constante définie mais jamais lue) |

### 4.2 Variables assignées mais jamais lues

| Fichier                             | Variable                                      |
| ----------------------------------- | --------------------------------------------- |
| `scraper/pipelines/scrap_bet.py:40` | `rapport_created`                             |
| `service/metrics.py:5`              | `count_courses` (shadowing + jamais retourné) |

### 4.3 Fichiers / modules entiers inutilisés

| Élément                        | Statut                    |
| ------------------------------ | ------------------------- |
| `service/metrics.py`           | Jamais importé, incomplet |
| Endpoints PMU (voir §2.11)     | Définis, jamais appelés   |
| Fonctions service (voir §2.12) | Définies, jamais appelées |

### 4.4 Dépendances `requirements.txt` suspectes

Fichier = dump `pip freeze` (~58 packages) plutôt que dépendances directes.

| Package                            | Utilisation dans le projet                                      |
| ---------------------------------- | --------------------------------------------------------------- |
| `pandas`, `numpy`                  | **Aucune**                                                      |
| `httpx`                            | **Aucune** (le client utilise `requests`)                       |
| `sentry-sdk`                       | **Aucune**                                                      |
| `fastapi-cli`, `fastapi-cloud-cli` | Probablement transitifs, pas nécessaires en prod                |
| `psycopg2` / `psycopg2-binary`     | **Utilisé implicitement** mais **absent** de `requirements.txt` |

→ **Exemple complet** : §12.18

---

## 5. Bugs critiques (P0)

### 5.1 Shadowing de `historize` — récursion infinie

```python
# api/routes/scrap.py
from scraper.pipelines.recuperation.historize import historize

@router.get("/historize")
async def historize(...):
    historize(start_date=start, end_date=end)  # appelle LA ROUTE, pas le pipeline
```

**Impact** : appel à `GET /scrap/historize` → `RecursionError`.

**Fix** : renommer la route ou aliaser l'import :

→ **Exemple complet** : §12.2 (avec trace d'exécution `RecursionError`)

### 5.2 Retry API PMU non fonctionnel

```python
# pmu/client.py
def fetch_pmu_api(url: str) -> dict | None:
    for _ in range(MAX_RETRIES):
        response = get(f"{BASE_URL}/{url}")
        if response.status_code == 200:
            return response.json()
        else:
            return None  # sort au 1er échec — la boucle ne sert à rien
    raise Exception(...)  # unreachable
```

**Impact** : aucune résilience face aux erreurs réseau transitoires.

→ **Exemple complet** : §12.4 (scénario 503 puis 200)

### 5.3 `service/metrics.py` — code cassé

```python
def calculate_metrics(session: Session) -> dict:
    count_courses = count_courses(session)  # shadowing du nom de fonction

def count_courses(session: Session) -> int:
    count = session.exec(select(Course)).count()  # .count() invalide sur Result SQLModel
    return count
```

Pas de `return` dans `calculate_metrics`. Fonction `count_courses` locale en conflit avec celle de `service/course.py`.

→ **Exemple complet** : §12.12

### 5.4 Log erroné dans `scrap_bet.py`

```python
# L26 — is_arrivee_definitive est la FONCTION, toujours truthy
logger.info(f"course {active_course} is {'active' if is_arrivee_definitive else 'not active'}")
# Devrait être : is_arrivee_definitive(course)
```

→ **Exemple complet** : §12.9 (log toujours « active »)

### 5.5 Absence de garde `None` — crashes probables

| Fichier                 | Ligne | Risque                                                                |
| ----------------------- | ----- | --------------------------------------------------------------------- |
| `scrap_courses.py`      | 21    | `programme['programme']` si `get_programme()` retourne `None`         |
| `scrap_participants.py` | 18    | `res['participants']` si `res is None`                                |
| `scrap_bet.py`          | 28    | `is_arrivee_definitive(course)` si `course is None`                   |
| `scrap_programmes.py`   | 16    | `programmes["programme"]` si réponse API vide                         |
| `service/course.py`     | 30-31 | `session.get(Course, course_id)` → `AttributeError` si course absente |

→ **Exemple complet** : §12.5 (guards), §12.8 (`set_course_is_over`)

### 5.6 Type hints incorrects

| Fichier                    | Problème                                                                  |
| -------------------------- | ------------------------------------------------------------------------- |
| `service/rapport.py:11`    | `get_rapports_definitifs_ids` → `List[Rapport]` mais retourne `List[str]` |
| `service/participant.py:5` | `-> None` mais `return participant`                                       |
| `service/reunion.py:5`     | `-> None` mais `return reunion`                                           |

→ **Exemple complet** : §12.16

### 5.7 `is_arrivee_definitive` — clé API potentiellement incorrecte

```python
# pmu/utils.py
def is_arrivee_definitive(course: Course) -> bool:
    return "arriveeDefinitive" in course.keys() and course["arriveeDefinitive"] == True
```

Le modèle Pydantic `Course` dans `api_types.py` expose aussi `isArriveeDefinitive`. La fonction ignore ce champ et cherche une clé qui peut ne pas exister dans la réponse brute.

→ **Exemple complet** : §12.10

---

## 6. Recommandations de robustesse

### 6.1 P0 — Immédiat (< 1 jour)

1. Corriger le shadowing `historize` dans `api/routes/scrap.py`.
2. Corriger `fetch_pmu_api` : continuer la boucle en cas d'échec, ajouter `timeout=30`, backoff exponentiel.
3. Corriger L26 `scrap_bet.py` : `is_arrivee_definitive(course)`.
4. Ajouter `if data is None: continue` dans tous les pipelines.
5. Supprimer ou corriger `service/metrics.py`.
6. Corriger les return types de `participant.py` et `reunion.py`.
7. Retirer les imports morts (`server.py`, `scrap_past_programmes.py`).

### 6.2 P1 — Fiabilité opérationnelle (1-3 jours)

8. **Session DB** : generator `get_db()` + `Depends()`, rollback automatique en cas d'exception.
9. **Batch commits** : une session par programme/course, pas par participant/rapport.
10. **Background tasks** : exécuter `historize` et scrapers longs via `BackgroundTasks` ou worker Celery/ARQ.
11. **Lifespan** : remplacer `@app.on_event` ; supprimer double exécution au startup.
12. **Validation PMU** : parser les réponses avec Pydantic (`Model.model_validate(response)`).
13. **Guard `set_course_is_over`** : vérifier que `course` existe avant mutation.
14. **Nettoyer `requirements.txt`** : deps directes + `psycopg2-binary`, retirer `pandas`/`numpy`.

### 6.3 P2 — Qualité / maintenabilité (1 semaine)

15. Extraire `Repository.upsert()` pour les 6 services.
16. **Tests** : unitaires sur `CourseIdentifier`, `ProgrammeIdentifier.increment`, `fetch_pmu_api` (mock), pipelines (mock DB).
17. **Outils** : `pyproject.toml` + ruff + mypy + pytest.
18. **README** : documenter variables d'env, endpoints, architecture.
19. **Logging structuré** : JSON logs, corrélation par pipeline/run.
20. **Healthcheck** : endpoint `/health` vérifiant DB + API PMU.

### 6.4 P3 — Architecture long terme

21. Séparer API HTTP et worker scraper (deux processus/containers).
22. Envisager FK + tables normalisées si requêtes analytiques prévues.
23. Migrer client HTTP vers `httpx` async si l'API reste async.
24. Auth / rate limiting sur les endpoints de scraping manuel.
25. CI/CD : lint + tests + migrations automatiques.

---

## 7. Problèmes FastAPI / async (synthèse)

| Problème                                | Fichier                 | Impact                                                          |
| --------------------------------------- | ----------------------- | --------------------------------------------------------------- |
| Routes `async` + code sync bloquant     | `scrap.py`, `server.py` | Event loop bloquée                                              |
| Pas de `BackgroundTasks` pour historize | `scrap.py`              | Réponse « started » mensongère                                  |
| Pas de gestion HTTP errors              | Toutes routes           | 500 générique                                                   |
| Query params sans validation Pydantic   | `scrap.py`              | `start_date: str = None` au lieu de `Optional[str]` + validator |
| Pas de CORS, auth, rate limiting        | `server.py`             | API ouverte                                                     |
| Route `/` déclenche scraping            | `server.py`             | Endpoint racine dangereux en prod                               |

---

## 8. Problèmes DB / session (synthèse)

```python
# service/deps.py
def get_session():
    return Session(engine)  # pas un generator, pas de Depends
```

| Problème                        | Détail                                |
| ------------------------------- | ------------------------------------- |
| Pas de `Depends(get_db)`        | Gestion manuelle partout              |
| Pas de rollback                 | `commit()` sans `try/except/rollback` |
| Commit par enregistrement       | N × commits dans les boucles          |
| `DATABASE_URL` peut être `None` | `create_engine(None)` → erreur opaque |
| Pas de pool config              | Engine minimal                        |
| `merge` sans vérification       | Écrase silencieusement                |

---

## 9. Tests, config, documentation

| Élément                       | État                                            |
| ----------------------------- | ----------------------------------------------- |
| Tests unitaires / intégration | **Aucun**                                       |
| `pytest`, `pytest-asyncio`    | Absents                                         |
| CI/CD                         | Non visible                                     |
| `.env`                        | Présent (probablement `DATABASE_URL`)           |
| `README.md`                   | Minimal (3 lignes, référence `venv` vs `.venv`) |
| Alembic                       | 4 migrations linéaires, cohérent avec models    |

→ **Exemple de tests à ajouter** : §12.19

---

## 10. Quick wins vs refactors majeurs

### Quick wins (< 1 jour)

- [ ] Renommer route `historize` (shadowing)
- [ ] Fix retry + timeout dans `pmu/client.py`
- [ ] Fix log L26 `scrap_bet.py`
- [ ] Supprimer imports morts
- [ ] Guards `None` dans pipelines
- [ ] Supprimer/fusionner `service/metrics.py`
- [ ] Nettoyer `requirements.txt`
- [ ] Corriger return types `participant.py` / `reunion.py`
- [ ] Retirer exécution immédiate redondante dans `startup_event`
- [ ] Retirer ou protéger la route `/` qui lance un scraping

### Refactors majeurs (plusieurs jours / semaines)

- [ ] Pattern repository + session DI FastAPI
- [ ] Worker background dédié (découpler scraping de l'API)
- [ ] Validation Pydantic systématique des réponses PMU
- [ ] Suite de tests (unit + intégration DB + mock PMU)
- [ ] Migration lifespan + suppression `@on_event`
- [ ] Refonte modèle DB (FK, relations) si besoin analytique
- [ ] CI avec lint + tests + migrations
- [ ] Séparation API / worker en deux services

---

## 11. Synthèse

Le projet possède une **ossature claire** adaptée à un scraper PMU, avec une séparation api / service / scraper / pmu / models bien pensée pour un prototype.

Il se trouve cependant en phase **pré-production** :

- **plusieurs bugs runtime confirmés** (shadowing historize, retry cassé, guards null absents) ;
- **zéro test** ;
- **gestion d'erreurs et sessions DB fragiles** ;
- **couche async FastAPI utilisée de façon contre-productive** ;
- **dette de duplication** (6× `create_*`, pipelines quasi identiques).

Les corrections P0 sont localisées et rapides (< 1 journée). La dette structurelle (sessions, batching, worker séparé) deviendra critique dès que le volume de données historisées augmentera.

---

## 12. Annexe — Exemples concrets « aujourd'hui » vs « demain »

Cette section complète les constats précédents avec du code réel tiré du projet, et des propositions explicites de ce que ça devrait ou pourrait devenir.

---

### 12.1 Injection de dépendances DB (`service/deps.py`)

#### Aujourd'hui

Chaque appelant ouvre sa propre session manuellement. Pas de rollback automatique.

```python
# service/deps.py
DATABASE_URL = os.getenv("DATABASE_URL")  # peut être None → crash opaque au démarrage
engine = create_engine(DATABASE_URL)

def get_session():
    return Session(engine)

# api/routes/metrics.py
@router.get("/")
def get_metrics():
    with get_session() as session:
        res_count_courses = count_courses(session)
        ...
```

**Ce qui se passe concrètement** : si une exception survient entre `merge()` et `commit()`, la session reste dans un état indéterminé. Chaque pipeline recrée une session à chaque boucle.

#### Demain (recommandé)

```python
# service/deps.py
from collections.abc import Generator
from fastapi import Depends

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def get_db() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# api/routes/metrics.py
@router.get("/")
def get_metrics(session: Session = Depends(get_db)):
    return {
        "count_courses": count_courses(session),
        "count_active_courses": count_active_courses(session),
        ...
    }
```

**Gain concret** : une session par requête HTTP, rollback garanti, testable via override FastAPI :

```python
# tests/conftest.py
def override_get_db():
    yield test_session

app.dependency_overrides[get_db] = override_get_db
```

---

### 12.2 Route `/scrap/historize` — shadowing et fausse promesse async

#### Aujourd'hui

```python
# api/routes/scrap.py (extrait réel)
from scraper.pipelines.recuperation.historize import historize, HIGHEST_DATE, LOWEST_DATE

@router.get("/historize")
async def historize(start_date: str = None, end_date: str = None):
    start = LOWEST_DATE
    end = HIGHEST_DATE
    if start_date and type(start_date) == str and start_date.isdigit() and len(start_date) == 8:
        start = ProgrammeIdentifier(start_date)
    if end_date and type(end_date) == str and end_date.isdigit() and len(end_date) == 8:
        end = ProgrammeIdentifier(end_date)
    historize(start_date=start, end_date=end)   # ← appelle la ROUTE, pas le pipeline
    return {"message": "Historization started"}
```

**Ce qui se passe concrètement** :

```
GET /scrap/historize
  → historize() route
    → historize() route
      → historize() route
        → RecursionError: maximum recursion depth exceeded
```

La réponse `{"message": "Historization started"}` laisse croire que le job tourne en arrière-plan, alors qu'en réalité (si le bug était corrigé) il bloquerait la requête pendant des heures.

#### Demain (minimum viable)

```python
from scraper.pipelines.recuperation.historize import historize as run_historize

@router.get("/historize")
def trigger_historize(start_date: str | None = None, end_date: str | None = None):
    start = parse_programme_date(start_date) or LOWEST_DATE
    end = parse_programme_date(end_date) or HIGHEST_DATE
    run_historize(start_date=start, end_date=end)
    return {"message": "Historization completed", "start": str(start), "end": str(end)}
```

#### Demain (recommandé — job long)

```python
from fastapi import BackgroundTasks

@router.post("/historize")
def trigger_historize(
    background_tasks: BackgroundTasks,
    start_date: str | None = None,
    end_date: str | None = None,
):
    start = parse_programme_date(start_date) or LOWEST_DATE
    end = parse_programme_date(end_date) or HIGHEST_DATE
    background_tasks.add_task(run_historize, start_date=start, end_date=end)
    return {"message": "Historization started", "start": str(start), "end": str(end)}
```

**Gain concret** : réponse immédiate, pas de blocage HTTP, nom de fonction sans ambiguïté.

---

### 12.3 Validation des dates programme

#### Aujourd'hui

Validation copiée-collée, verbeuse, sans message d'erreur clair :

```python
# api/routes/scrap.py
if start_date and type(start_date) == str and start_date.isdigit() and len(start_date) == 8:
    start = ProgrammeIdentifier(start_date)
```

Un appel `GET /scrap/historize?start_date=32082026` (date invalide) est silencieusement ignoré → on scrape depuis `LOWEST_DATE` sans que l'utilisateur le sache.

#### Demain

```python
# pmu/utils.py
from fastapi import HTTPException

def parse_programme_date(value: str | None) -> ProgrammeIdentifier | None:
    if value is None:
        return None
    if not (value.isdigit() and len(value) == 8):
        raise HTTPException(status_code=422, detail=f"Invalid programme date: {value!r}, expected DDMMYYYY")
    try:
        programme_date_to_date(value)  # lève ValueError si jour/mois incohérent
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid calendar date: {value!r}")
    return ProgrammeIdentifier(value)

# api/routes/scrap.py
start = parse_programme_date(start_date) or LOWEST_DATE
```

**Gain concret** : erreur HTTP 422 explicite au lieu d'un comportement silencieux.

---

### 12.4 Client HTTP PMU — retry et timeout

#### Aujourd'hui

```python
# pmu/client.py (extrait réel)
def fetch_pmu_api(url: str) -> dict | None:
    for _ in range(MAX_RETRIES):          # boucle inutile
        response = get(f"{BASE_URL}/{url}")  # pas de timeout → peut pendre indéfiniment
        if response.status_code == 200:
            return response.json()
        else:
            return None                   # sort au 1er échec
    raise Exception(...)                  # jamais atteint
```

**Scénario concret** : l'API PMU répond `503` une fois puis `200` → le code retourne `None` immédiatement, le pipeline crashe ou skip silencieusement.

#### Demain

```python
import time
from requests import get, RequestException

def fetch_pmu_api(url: str) -> dict | None:
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = get(f"{BASE_URL}/{url}", timeout=30)
            if response.status_code == 200:
                return response.json()
            last_error = f"HTTP {response.status_code}"
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES} failed for {url}: {last_error}")
        except RequestException as exc:
            last_error = str(exc)
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES} failed for {url}: {last_error}")
        if attempt < MAX_RETRIES:
            time.sleep(2 ** attempt)  # backoff : 2s, 4s, 8s
    logger.error(f"All retries exhausted for {url}: {last_error}")
    return None
```

**Gain concret** : 3 vraies tentatives, timeout 30s, logs exploitables.

---

### 12.5 Pipelines — absence de garde `None`

#### Aujourd'hui

```python
# scraper/pipelines/scrap_courses.py (extrait réel)
programme = get_programme(ProgrammeIdentifier(programme_date))
reunions = programme['programme']['reunions']   # TypeError si programme is None
```

```python
# scraper/pipelines/scrap_participants.py (extrait réel)
res = get_participants(course_identifier)
logger.info(f"scraping {len(res['participants'])} participants ...")  # TypeError si res is None
```

```python
# scraper/pipelines/scrap_bet.py (extrait réel)
course = get_course(active_course)
...
if is_arrivee_definitive(course):   # TypeError si course is None
```

**Scénario concret** : coupure réseau PMU → `fetch_pmu_api` retourne `None` → crash du pipeline entier, les courses suivantes ne sont jamais traitées.

#### Demain

```python
# scraper/pipelines/scrap_courses.py
programme = get_programme(ProgrammeIdentifier(programme_date))
if programme is None:
    logger.warning(f"No programme data for {programme_date}, skipping")
    continue

programme_data = programme.get("programme")
if not programme_data:
    logger.warning(f"Missing 'programme' key for {programme_date}, skipping")
    continue

reunions = programme_data.get("reunions") or []
```

**Pattern réutilisable pour tous les pipelines** :

```python
def require_key(data: dict | None, key: str, context: str) -> dict | list | None:
    if data is None:
        logger.warning(f"{context}: response is None")
        return None
    if key not in data:
        logger.warning(f"{context}: missing key {key!r}")
        return None
    return data[key]
```

---

### 12.6 Sessions DB — un commit par enregistrement

#### Aujourd'hui

Pour un programme avec 8 réunions × 10 courses = **88 sessions + 88 commits** :

```python
# scraper/pipelines/scrap_courses.py (extrait réel)
for reunion in reunions:
    with get_session() as session:
        create_reunion(ReunionCreate(...), session)   # commit #1
    for course in courses:
        with get_session() as session:
            create_course(CourseCreate(...), session)  # commit #2, #3, #4...
```

Idem dans `scrap_participants.py` : **1 commit par participant**.

#### Demain

Une session par programme, un seul commit en fin de traitement :

```python
def scrap_courses():
    with get_session() as session:
        programme_dates = get_not_scraped_programme_dates(session)

    for programme_date in programme_dates:
        programme = get_programme(ProgrammeIdentifier(programme_date))
        if programme is None:
            continue

        reunions = programme.get("programme", {}).get("reunions") or []

        with get_session() as session:
            for reunion in reunions:
                reunion_number = reunion["numOfficiel"]
                session.merge(Reunion.model_validate(
                    ReunionCreate(id=f"{programme_date}/R{reunion_number}", raw=reunion)
                ))
                for course in reunion.get("courses", []):
                    course_number = course["numExterne"]
                    session.merge(Course.model_validate(
                        CourseCreate(id=f"{programme_date}/R{reunion_number}/C{course_number}", raw=course)
                    ))
            set_programme_scraped(ProgrammeIdentifier(programme_date), session)
            session.commit()  # 1 seul commit pour tout le programme
```

**Gain concret** : pour 1000 courses → 1 commit au lieu de 1000. Rollback atomique si une insertion échoue.

---

### 12.7 Pattern `create_*` dupliqué — 6 services identiques

#### Aujourd'hui

Le même code copié dans 6 fichiers :

```python
# service/course.py, programme.py, rapport.py, combinaison.py, participant.py, reunion.py
def create_course(course_create: CourseCreate, session: Session) -> Course:
    course = Course.model_validate(course_create)
    session.merge(course)
    session.commit()
    return course
```

#### Demain (option légère)

```python
# service/repository.py
from typing import TypeVar
from sqlmodel import Session, SQLModel

T = TypeVar("T", bound=SQLModel)

def upsert(session: Session, create_model: SQLModel, table_model: type[T]) -> T:
    entity = table_model.model_validate(create_model)
    session.merge(entity)
    return entity

# service/course.py
def create_course(course_create: CourseCreate, session: Session, *, commit: bool = True) -> Course:
    course = upsert(session, course_create, Course)
    if commit:
        session.commit()
    return course
```

#### Demain (option structurée)

```python
# service/repository.py
class Repository(Generic[T]):
    def __init__(self, model: type[T]):
        self.model = model

    def upsert(self, session: Session, data: SQLModel, *, commit: bool = False) -> T:
        entity = self.model.model_validate(data)
        session.merge(entity)
        if commit:
            session.commit()
        return entity

course_repo = Repository(Course)
programme_repo = Repository(Programme)
```

**Gain concret** : un seul endroit pour ajouter du logging, du retry, ou du `flush()` sans commit.

---

### 12.8 `set_course_is_over` — crash si course absente

#### Aujourd'hui

```python
# service/course.py (extrait réel)
def set_course_is_over(course_identifier: CourseIdentifier, session: Session) -> Course:
    course_id = str(course_identifier)
    course = session.get(Course, course_id)
    course.is_over = True          # AttributeError: 'NoneType' object has no attribute 'is_over'
    session.merge(course)
    session.commit()
    return course
```

#### Demain

```python
def set_course_is_over(course_identifier: CourseIdentifier, session: Session) -> Course | None:
    course_id = str(course_identifier)
    course = session.get(Course, course_id)
    if course is None:
        logger.warning(f"Course {course_id} not found, cannot mark as over")
        return None
    course.is_over = True
    session.merge(course)
    session.commit()
    return course
```

---

### 12.9 Log erroné dans `scrap_bet.py`

#### Aujourd'hui

```python
# scraper/pipelines/scrap_bet.py L26 (extrait réel)
logger.info(f"course {active_course} is {'active' if is_arrivee_definitive else 'not active'}")
```

**Ce qui est loggé** : toujours `"course 08082026/R1/C3 is active"` car `is_arrivee_definitive` (la fonction) est toujours truthy en Python.

#### Demain

```python
is_over = is_arrivee_definitive(course) if course else False
logger.info(f"course {active_course} arrivee_definitive={is_over}")
```

---

### 12.10 `is_arrivee_definitive` — clé API incertaine

#### Aujourd'hui

```python
# pmu/utils.py (extrait réel)
def is_arrivee_definitive(course: Course) -> bool:
    return "arriveeDefinitive" in course.keys() and course["arriveeDefinitive"] == True
```

Le type hint dit `Course` (Pydantic) mais on reçoit un `dict` brut. La clé `arriveeDefinitive` peut ne pas exister ; le modèle Pydantic utilise `isArriveeDefinitive`.

#### Demain

```python
def is_arrivee_definitive(course: dict | None) -> bool:
    if course is None:
        return False
    # couvrir les deux conventions possibles de l'API PMU
    if course.get("isArriveeDefinitive") is True:
        return True
    if course.get("arriveeDefinitive") is True:
        return True
    return False
```

Ou, si validation Pydantic en amont :

```python
def is_arrivee_definitive(course: Course) -> bool:
    return course.isArriveeDefinitive is True
```

---

### 12.11 Validation Pydantic des réponses PMU

#### Aujourd'hui

```python
# pmu/endpoints.py (extrait réel)
def get_programme(programme_identifier: ProgrammeIdentifier) -> ProgrammeResponse | None:
    response = fetch_pmu_api(str(programme_identifier))
    return response   # dict brut, annotation mensongère

# scraper/pipelines/scrap_programmes.py
programmes_disponibles = programmes["programme"]["datesProgrammesDisponibles"]
# KeyError possible si la structure change
```

#### Demain

```python
# pmu/endpoints.py
def get_programme(programme_identifier: ProgrammeIdentifier) -> ProgrammeResponse | None:
    response = fetch_pmu_api(str(programme_identifier))
    if response is None:
        return None
    try:
        return ProgrammeResponse.model_validate(response)
    except ValidationError as exc:
        logger.error(f"Invalid programme response for {programme_identifier}: {exc}")
        return None

# scraper/pipelines/scrap_programmes.py
programme = get_programme(programme_identifier)
if programme is None:
    return
dates = programme.programme.datesProgrammesDisponibles  # accès typé, autocomplétion IDE
```

**Gain concret** : détection immédiate si l'API PMU change de format, au lieu d'un `KeyError` en prod.

---

### 12.12 Métriques — duplication et fichier mort

#### Aujourd'hui

Trois endroits, dont un cassé :

```python
# service/metrics.py (FICHIER ENTIER — jamais importé)
def calculate_metrics(session: Session) -> dict:
    count_courses = count_courses(session)   # shadowing + pas de return

def count_courses(session: Session) -> int:
    count = session.exec(select(Course)).count()  # API SQLModel incorrecte
    return count

# api/routes/metrics.py (utilisé en prod — correct)
def get_metrics():
    with get_session() as session:
        return {"count_courses": count_courses(session), ...}  # appelle service/course.py
```

#### Demain

Supprimer `service/metrics.py`. Centraliser :

```python
# service/metrics.py (refactorisé)
from pydantic import BaseModel

class MetricsResponse(BaseModel):
    count_courses: int
    count_active_courses: int
    count_inactive_courses: int
    count_rapports: int

def get_all_metrics(session: Session) -> MetricsResponse:
    return MetricsResponse(
        count_courses=count_courses(session),
        count_active_courses=count_active_courses(session),
        count_inactive_courses=count_inactive_courses(session),
        count_rapports=count_rapports(session),
    )

# api/routes/metrics.py
@router.get("/", response_model=MetricsResponse)
def get_metrics(session: Session = Depends(get_db)):
    return get_all_metrics(session)
```

---

### 12.13 Planification au démarrage — triple `@on_event`

#### Aujourd'hui

```python
# server.py (extrait réel)
@app.on_event('startup')
@repeat_every(seconds=60 * 5)
def every_five_minutes_task():
    every_five_minutes()

@app.on_event('startup')
@repeat_at(cron='0 4 * * *')
def every_day_task():
    every_day()

@app.on_event('startup')
def startup_event():
    setup_logging()
    every_day()           # scraping complet IMMÉDIAT au boot
    every_five_minutes()  # idem
```

**Timeline concrète au démarrage** :

```
t=0s   → setup_logging()
t=0s   → every_day()        (scrap programmes + courses + participants)
t=0s   → every_five_minutes() (scrap bets pour toutes les courses actives)
t=0s   → repeat_every enregistré (prochain run dans 5 min)
t=0s   → repeat_at enregistré (prochain run à 4h)
```

Résultat : double/triple charge au boot, API indisponible pendant le scraping.

#### Demain (lifespan moderne)

```python
# server.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    # Option A : ne PAS lancer de scraping au boot
    # Option B : lancer uniquement en dev via variable d'env
    if os.getenv("RUN_SCRAPERS_ON_STARTUP") == "true":
        every_day()
        every_five_minutes()
    yield
    # teardown si nécessaire

app = FastAPI(lifespan=lifespan)

@app.on_event("startup")  # ou intégrer repeat_every dans lifespan
@repeat_every(seconds=60 * 5)
def every_five_minutes_task():
    every_five_minutes()
```

#### Demain (architecture cible — worker séparé)

```
┌─────────────────┐     ┌──────────────────┐
│  API FastAPI    │     │  Worker scraper  │
│  (port 8080)    │     │  (cron / queue)  │
│  - /metrics     │     │  - every_day()   │
│  - /scrap/*     │     │  - every_5min()  │
│  - /health      │     │  - historize()   │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
              PostgreSQL
```

---

### 12.14 Route `/` qui lance un scraping

#### Aujourd'hui

```python
# server.py (extrait réel)
@app.get("/")
async def read_root():
    return scrap_programmes()   # chaque visite du site = appel API PMU + écritures DB
```

**Scénario concret** : un health-check Kubernetes ou un bot qui ping `/` toutes les 30s → scraping continu involontaire.

#### Demain

```python
@app.get("/")
def read_root():
    return {"service": "epmu-server", "status": "ok"}

@app.get("/health")
def health(session: Session = Depends(get_db)):
    session.exec(select(func.count(Course.id))).first()  # vérifie la DB
    return {"status": "healthy"}
```

---

### 12.15 `CourseIdentifier` — double constructeur

#### Aujourd'hui

```python
# pmu/types/types.py (extrait réel)
class CourseIdentifier:
    def __init__(self, course_num: int, reunion_num: int, programme: str):
        self.course_num = course_num
        ...
    def __init__(self, course_id: str):   # écrase le précédent
        self.course_num = int(course_id.split('/')[-1].split('C')[1])
        ...
```

```python
# Ce code NE MARCHE PAS (silencieusement remplacé par le 2e __init__) :
CourseIdentifier(3, 1, "08082026")

# Seul ça marche :
CourseIdentifier("08082026/R1/C3")
```

#### Demain

```python
class CourseIdentifier:
    def __init__(self, course_id: str | None = None, *, course_num: int = None,
                 reunion_num: int = None, programme: str = None):
        if course_id is not None:
            parts = course_id.split("/")
            self.programme = parts[0]
            self.reunion_num = int(parts[1].split("R")[1])
            self.course_num = int(parts[2].split("C")[1])
        elif all(v is not None for v in (course_num, reunion_num, programme)):
            self.course_num = course_num
            self.reunion_num = reunion_num
            self.programme = programme
        else:
            raise ValueError("Provide course_id or (course_num, reunion_num, programme)")
```

Ou plus simple : un seul constructeur `from_string()` + `@classmethod from_parts()`.

---

### 12.16 Type hints incorrects

#### Aujourd'hui

```python
# service/rapport.py
def get_rapports_definitifs_ids(session: Session) -> List[Rapport]:  # ment : retourne List[str]
    return session.exec(select(Rapport.id)).all()

# service/participant.py
def create_participant(...) -> None:   # ment : retourne Participant
    ...
    return participant
```

**Impact concret** : mypy/IDE ne détectent pas les erreurs ; un appelant qui fait `rapport.raw` sur le résultat crashe à l'exécution.

#### Demain

```python
def get_rapports_definitifs_ids(session: Session) -> list[str]:
    return session.exec(select(Rapport.id)).all()

def create_participant(participant_create: ParticipantCreate, session: Session) -> Participant:
    participant = Participant.model_validate(participant_create)
    session.merge(participant)
    session.commit()
    return participant
```

---

### 12.17 `scrap_programmes` vs `scrap_past_programmes` — quasi doublon

#### Aujourd'hui

```python
# scraper/pipelines/scrap_programmes.py — scrape les dates du jour
programme = get_programme(ProgrammeIdentifier(programme_date))
create_programme(ProgrammeCreate(id=programme_date, raw=programme), session)

# scraper/pipelines/scrap_past_programmes.py — scrape une date passée
programme = get_programme(programme_identifier)
create_programme(ProgrammeCreate(id=str(programme_identifier), raw=programme), session)
```

Deux fichiers, même logique, imports morts dans le second (`date`, `date_to_programme_date`).

#### Demain

```python
# scraper/pipelines/scrap_programme.py
def scrap_programme(programme_identifier: ProgrammeIdentifier) -> bool:
    programme = get_programme(programme_identifier)
    if programme is None:
        logger.warning(f"No data for {programme_identifier}")
        return False
    with get_session() as session:
        create_programme(
            ProgrammeCreate(id=str(programme_identifier), raw=programme),
            session,
        )
    return True

def scrap_programmes():
    today = ProgrammeIdentifier(date_to_programme_date(date.today()))
    meta = get_programme(today)
    if meta is None:
        return
    for programme_date in meta.get("programme", {}).get("datesProgrammesDisponibles", []):
        scrap_programme(ProgrammeIdentifier(programme_date))
```

---

### 12.18 `requirements.txt` — dump vs deps intentionnelles

#### Aujourd'hui

```
# requirements.txt (58 lignes, pip freeze)
numpy==2.5.1          # jamais importé
pandas==3.0.3         # jamais importé
httpx==0.28.1         # jamais importé (on utilise requests)
sentry-sdk==2.66.0    # jamais importé
# psycopg2 ABSENT     # pourtant requis par PostgreSQL
```

#### Demain

```
# requirements.txt (deps directes uniquement)
fastapi>=0.139
uvicorn[standard]>=0.51
sqlmodel>=0.0.39
alembic>=1.19
psycopg2-binary>=2.9
requests>=2.34
python-dotenv>=1.2
fastapi-utilities>=0.3.1

# requirements-dev.txt
pytest>=8.0
ruff>=0.8
```

---

### 12.19 Exemple de test manquant (à ajouter)

Aujourd'hui : **0 test**. Voici à quoi pourrait ressembler la base :

```python
# tests/test_course_identifier.py
import pytest
from pmu.types.types import CourseIdentifier

def test_course_identifier_from_string():
    cid = CourseIdentifier("08082026/R1/C3")
    assert str(cid) == "08082026/R1/C3"
    assert cid.programme == "08082026"
    assert cid.reunion_num == 1
    assert cid.course_num == 3

def test_course_identifier_ordering():
    assert CourseIdentifier("08082026/R1/C1") < CourseIdentifier("08082026/R1/C2")

# tests/test_fetch_pmu_api.py
from unittest.mock import patch, MagicMock
from pmu.client import fetch_pmu_api

@patch("pmu.client.get")
def test_fetch_pmu_api_retries_on_failure(mock_get):
    mock_get.side_effect = [
        MagicMock(status_code=503),
        MagicMock(status_code=200, json=lambda: {"ok": True}),
    ]
    result = fetch_pmu_api("08082026")
    assert result == {"ok": True}
    assert mock_get.call_count == 2
```

---

### 12.20 Tableau récapitulatif des transformations

| Zone               | Aujourd'hui        | Demain (effort)            | Impact           |
| ------------------ | ------------------ | -------------------------- | ---------------- |
| `historize` route  | Récursion infinie  | Renommer + BackgroundTasks | Critique         |
| `fetch_pmu_api`    | 0 retry réel       | Boucle + timeout + backoff | Critique         |
| Pipelines          | Crash sur `None`   | Guards + logs              | Critique         |
| Sessions DB        | N commits/boucle   | 1 commit/batch             | Performance      |
| `create_*` × 6     | Copier-coller      | `Repository.upsert`        | Maintenabilité   |
| `@on_event` × 3    | Scraping au boot   | Lifespan / worker séparé   | Stabilité        |
| Route `/`          | Lance scraping     | Healthcheck                | Sécurité ops     |
| Types PMU          | `dict` non validé  | Pydantic `model_validate`  | Robustesse       |
| Tests              | Aucun              | pytest + mocks             | Confiance        |
| `requirements.txt` | pip freeze 58 pkgs | ~8 deps directes           | Reproductibilité |

---

## 13. Parallélisme HTTP — le server traite-t-il plusieurs requêtes en parallèle ?

### 13.1 Réponse courte

**Partiellement, mais de façon très limitée aujourd'hui.**

| Composant                                          | Parallèle aujourd'hui ? | Pourquoi                                                     |
| -------------------------------------------------- | ----------------------- | ------------------------------------------------------------ |
| Requêtes HTTP légères (`GET /metrics/`)            | Oui, en pratique        | Route sync courte ; Starlette peut les dispatcher            |
| Requêtes longues (`GET /`, `GET /scrap/historize`) | **Non (effectif)**      | Code sync bloquant dans routes `async` → bloque l'event loop |
| Scrapers planifiés (`repeat_every`, `repeat_at`)   | **Non entre eux**       | Même processus, exécution synchrone séquentielle             |
| HTTP + cron en même temps                          | **Très mal**            | Un scraping long monopolise le processus                     |

---

### 13.2 Ce qui se passe concrètement aujourd'hui

#### Architecture runtime actuelle

```
┌─────────────────────────────────────────────────────────┐
│  1 processus Uvicorn (1 worker par défaut)              │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Event loop asyncio (FastAPI / Starlette)        │   │
│  │                                                  │   │
│  │  GET /metrics  ──► sync court ──► OK             │   │
│  │  GET /         ──► async read_root()             │   │
│  │       └─► scrap_programmes()  ◄── BLOQUE TOUT    │   │
│  │  GET /scrap/historize ──► async historize()      │   │
│  │       └─► historize() sync     ◄── BLOQUE TOUT   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  repeat_every (5 min) ──► scrap_bet()  ◄── BLOQUE TOUT  │
│  repeat_at (4h)       ──► every_day()  ◄── BLOQUE TOUT  │
│  startup              ──► every_day() + scrap_bet()     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                   PostgreSQL (engine partagé)
```

#### Code responsable du blocage

```python
# server.py — route async MAIS appel sync bloquant
@app.get("/")
async def read_root():
    return scrap_programmes()   # requests + DB, peut durer plusieurs secondes/minutes

# api/routes/scrap.py
@router.get("/historize")
async def historize(...):
    historize(...)   # boucle sur des années de programmes — très long
    return {"message": "Historization started"}

# api/routes/metrics.py — route sync courte (OK pour la concurrence)
@router.get("/")
def get_metrics():
    with get_session() as session:
        return {"count_courses": count_courses(session), ...}
```

**Règle clé** : une fonction `async def` qui appelle du code synchrone bloquant (`requests.get`, `session.commit`, boucles longues) **sans** `await run_in_executor(...)` monopolise l'event loop. Les autres requêtes HTTP attendent.

#### Uvicorn : 1 worker par défaut

```python
# server.py
uvicorn.run(app, host="0.0.0.0", port=8080)   # workers=1 implicite
```

Avec 1 worker = 1 processus = 1 event loop. Même avec `--workers 4`, chaque worker relancerait les scrapers au startup (problème actuel × 4).

---

### 13.3 Scénarios concrets

#### Scénario A — deux requêtes `/metrics` en parallèle

```
Client 1 ──► GET /metrics/ ──► ~50ms DB ──► 200 OK
Client 2 ──► GET /metrics/ ──► ~50ms DB ──► 200 OK   ✅ Les deux passent
```

Fonctionne car la route est sync courte et la DB répond vite.

#### Scénario B — scraping + metrics en parallèle

```
t=0s   Client 1 ──► GET /  ──► scrap_programmes() démarre (30s)
t=1s   Client 2 ──► GET /metrics/ ──► ATTEND que scrap_programmes finisse
t=30s  Client 2 reçoit enfin sa réponse                      ❌
```

#### Scénario C — cron + requête HTTP

```
t=0s   repeat_every déclenche scrap_bet() (2 min)
t=10s  Client ──► GET /metrics/ ──► bloqué jusqu'à t=120s    ❌
```

---

### 13.4 Limites techniques actuelles

| Limite                          | Détail                                                         |
| ------------------------------- | -------------------------------------------------------------- |
| Event loop bloquée              | Routes `async` + code sync                                     |
| 1 worker Uvicorn                | Pas de parallélisme multi-processus                            |
| Scrapers dans le même processus | Cron et API se marchent dessus                                 |
| `Session` SQLAlchemy            | **Non thread-safe** — 1 session par thread/requête obligatoire |
| `engine` SQLAlchemy             | Thread-safe via pool de connexions (OK partagé)                |
| Pas de verrou sur scrapers      | Deux triggers simultanés → double scraping                     |

---

### 13.5 Comment mettre en place le parallélisme HTTP

#### Niveau 1 — Quick wins (< 1 jour, même architecture)

**A. Retirer le faux async**

```python
# Aujourd'hui (bloque l'event loop)
@app.get("/")
async def read_root():
    return scrap_programmes()

# Demain — option 1 : route sync (Starlette utilise un thread pool)
@app.get("/")
def read_root():
    return {"service": "epmu-server", "status": "ok"}   # ne plus scraper ici

# Demain — option 2 : déléguer en arrière-plan
from fastapi import BackgroundTasks

@app.post("/scrap/programmes")
def trigger_scrap_programmes(background_tasks: BackgroundTasks):
    background_tasks.add_task(scrap_programmes)
    return {"status": "started"}
```

**B. Ne plus lancer les scrapers dans les routes de consultation**

La route `/` ne doit pas déclencher de scraping (cf. §12.14).

**Gain** : `/metrics` reste disponible pendant un scraping manuel lancé en background.

**Limite** : `BackgroundTasks` tourne toujours dans le **même processus** — un gros job occupe quand même des ressources CPU/DB.

---

#### Niveau 2 — Parallélisme HTTP réel (1-2 jours)

**A. Séparer routes sync courtes et jobs longs**

```python
# Routes API : uniquement sync court ou async avec await réel
@router.get("/metrics/")
def get_metrics(session: Session = Depends(get_db)):
    return get_all_metrics(session)

# Jobs longs : POST + BackgroundTasks ou file de messages
@router.post("/scrap/historize")
def trigger_historize(background_tasks: BackgroundTasks, ...):
    background_tasks.add_task(run_historize, start_date=start, end_date=end)
    return {"status": "started"}
```

**B. Multi-workers Uvicorn (requêtes HTTP indépendantes)**

```bash
# 4 processus = 4 requêtes HTTP lourdes en parallèle (si sync/executor)
uvicorn server:app --host 0.0.0.0 --port 8080 --workers 4
```

**Attention** : avec le code actuel, chaque worker exécute `startup_event()` → 4× scraping au boot. Il faut d'abord retirer le scraping du startup (cf. §12.13).

**C. Pool de threads pour code sync dans routes async (si vous gardez async)**

```python
import asyncio
from functools import partial

@app.get("/scrap/programmes")
async def trigger_scrap_programmes():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, scrap_programmes)  # None = ThreadPoolExecutor default
    return {"status": "done"}
```

**Gain** : l'event loop reste libre pour `/metrics` pendant qu'un thread exécute le scraper.

---

#### Niveau 3 — Architecture cible (recommandée, plusieurs jours)

Séparer **API** et **worker scraper** :

```
┌──────────────────┐         ┌─────────────────────┐
│  API (Uvicorn)   │         │  Worker scraper     │
│  workers=2-4     │         │  (process dédié)    │
│                  │         │                     │
│  GET /metrics    │         │  cron every 5 min   │
│  POST /scrap/*   │──queue─►│  cron every day     │
│  GET /health     │         │  historize batch    │
└────────┬─────────┘         └──────────┬──────────┘
         │                              │
         └──────────────┬───────────────┘
                        ▼
                   PostgreSQL
```

Options de queue : Redis + ARQ, Celery, ou simple table `jobs` en DB.

**Gain** :

- L'API répond toujours vite ;
- le worker peut utiliser du multithreading sans impacter les requêtes HTTP ;
- un seul worker scraper → pas de double exécution des crons.

---

### 13.6 Tableau récap — parallélisme HTTP

| Approche                        | Effort | Parallèle HTTP ?         | Scraping pendant requêtes ? |
| ------------------------------- | ------ | ------------------------ | --------------------------- |
| État actuel                     | —      | Partiel (routes courtes) | ❌ Non                      |
| Retirer async + BackgroundTasks | Faible | Moyen                    | ⚠️ Même processus           |
| `run_in_executor`               | Faible | Bon                      | ⚠️ Même processus           |
| `--workers 4`                   | Moyen  | Bon (multi-process)      | ⚠️ Si startup corrigé       |
| API + worker séparé             | Élevé  | ✅ Excellent             | ✅ Oui                      |

---

## 14. Parallélisme des pipelines — multithreading des appels PMU

### 14.1 Réponse courte

**Non, aucun pipeline n'est parallélisé aujourd'hui.** Tout est séquentiel : une boucle `for`, un appel HTTP, une écriture DB, puis l'élément suivant.

Le goulot d'étranglement principal est **l'I/O réseau** (appels `requests.get` vers l'API PMU) — c'est précisément ce qu'un multithreading ou asyncio peut accélérer.

---

### 14.2 État actuel — exécution séquentielle

#### Orchestrateur

```python
# scraper/orchestrator.py (extrait réel)
def every_day():
    scrap_programmes.scrap_programmes()      # finit avant...
    scrap_courses.scrap_courses()            # ...de commencer
    scrap_participants.scrap_participants()   # ...celui-ci

def every_five_minutes():
    scrap_bet.scrap_bet()
```

3 pipelines en série chaque matin. Pas de parallélisme inter-pipelines.

#### Exemple chiffré — `scrap_participants`

```python
# scraper/pipelines/scrap_participants.py (extrait réel)
for course_identifier in course_identifiers:          # ex. 40 courses actives
    res = get_participants(course_identifier)         # ~200-500ms HTTP chacun
    for participant in participants:
        with get_session() as session:
            create_participant(...)                 # ~10-30ms DB chacun
```

**Estimation** (40 courses, 12 participants/course, 300ms HTTP + 20ms DB/participant) :

| Phase                  | Calcul     | Durée     |
| ---------------------- | ---------- | --------- |
| HTTP seul (séquentiel) | 40 × 300ms | **~12 s** |
| DB seule (séquentiel)  | 480 × 20ms | **~10 s** |
| **Total séquentiel**   |            | **~22 s** |

Avec parallélisation HTTP (10 threads) + batch DB :

| Phase                        | Calcul             | Durée      |
| ---------------------------- | ------------------ | ---------- |
| HTTP (10 threads)            | 40/10 × 300ms      | **~1,2 s** |
| DB (1 session, batch commit) | 1 commit/programme | **~2 s**   |
| **Total optimisé**           |                    | **~3-4 s** |

**Gain potentiel : ×5 à ×10** sur les pipelines dominés par l'HTTP.

#### Pipelines et leur profil I/O

| Pipeline             | Boucle principale         | Appels HTTP/cycle                         | Parallelisable ?           |
| -------------------- | ------------------------- | ----------------------------------------- | -------------------------- |
| `scrap_programmes`   | dates disponibles (~5-20) | 1 + N dates                               | ✅ Oui (fetch dates)       |
| `scrap_courses`      | réunions × courses        | 1/programme                               | ⚠️ Partiel (par programme) |
| `scrap_participants` | courses actives (~40)     | 1/course                                  | ✅ **Excellent candidat**  |
| `scrap_bet`          | courses actives           | 3/course (course, combinaisons, rapports) | ✅ **Excellent candidat**  |
| `historize`          | années × jours            | 1/jour                                    | ✅ Oui (avec rate limit)   |

---

### 14.3 Pourquoi le multithreading est adapté ici

```
CPU (parsing JSON, merge SQLModel)  ██░░░░░░░░  ~10% du temps
Réseau (requests.get PMU)           ████████░░  ~70% du temps
DB (commit)                         ██░░░░░░░░  ~20% du temps
```

Les appels PMU sont **I/O-bound** : le thread attend la réponse réseau. Pendant ce temps, d'autres threads peuvent travailler. Le GIL Python n'est pas un problème pour l'I/O.

**`requests` est synchrone** → `ThreadPoolExecutor` est la solution la plus simple sans réécrire tout en async.

---

### 14.4 Contraintes à respecter avant de paralléliser

| Contrainte                | Raison                                               | Solution                                                            |
| ------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------- |
| `Session` non thread-safe | Crash ou corruption si 2 threads partagent 1 session | 1 session par thread, ou fetch parallèle + write séquentiel         |
| Rate limiting API PMU     | Trop de requêtes simultanées → 429/503               | Limiter `max_workers` (5-10) + backoff                              |
| Ordre des commits         | Pas critique pour du scraping brut                   | Batch commit en fin de boucle                                       |
| Logs entremêlés           | Difficile à lire                                     | `logger` thread-safe en Python, ajouter `course_id` dans chaque log |
| Double scraping           | 2 workers cron en parallèle                          | Mutex / un seul worker scraper                                      |

---

### 14.5 Pattern recommandé — « fetch parallèle, write séquentiel »

C'est le pattern le plus sûr avec SQLAlchemy/SQLModel :

```
Phase 1 (parallèle) : N threads → fetch PMU → résultats en mémoire
Phase 2 (séquentiel) : 1 session → merge all → 1 commit
```

#### Aujourd'hui — `scrap_participants`

```python
for course_identifier in course_identifiers:
    res = get_participants(course_identifier)           # HTTP séquentiel
    for participant in res['participants']:
        with get_session() as session:
            create_participant(..., session)          # N commits
```

#### Demain — avec ThreadPoolExecutor

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = 8  # ajuster selon tolérance API PMU

def fetch_participants(course_identifier):
    res = get_participants(course_identifier)
    if res is None:
        return course_identifier, []
    return course_identifier, res.get("participants", [])

def scrap_participants():
    with get_session() as session:
        course_identifiers = get_active_courses_identifiers(session)

    # Phase 1 : fetch parallèle (I/O)
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(fetch_participants, cid): cid
            for cid in course_identifiers
        }
        for future in as_completed(futures):
            course_id, participants = future.result()
            results.append((course_id, participants))

    # Phase 2 : write séquentiel (1 session, 1 commit)
    with get_session() as session:
        for course_id, participants in results:
            for participant in participants:
                session.merge(Participant.model_validate(
                    ParticipantCreate(
                        id=f"{course_id}/P{participant['numPmu']}",
                        raw=participant,
                    )
                ))
        session.commit()
```

**Gain estimé** : pour 40 courses × 300ms → **12s → ~1,5s** en phase fetch.

---

### 14.6 Application par pipeline

#### `scrap_bet` — 3 appels HTTP par course

```python
def fetch_bet_data(course_identifier):
    """Exécutable en parallèle — pas de session DB ici."""
    return {
        "course_id": course_identifier,
        "course": get_course(course_identifier),
        "combinaisons": get_combinaisons(course_identifier),
        "rapports": None,  # rempli seulement si arrivee definitive
    }

def scrap_bet():
    with get_session() as session:
        active_courses = get_active_courses_identifiers(session)

    # Fetch parallèle
    with ThreadPoolExecutor(max_workers=8) as executor:
        fetched = list(executor.map(fetch_bet_data, active_courses))

    # Write séquentiel
    with get_session() as session:
        for data in fetched:
            course = data["course"]
            if data["combinaisons"]:
                for combinaison in data["combinaisons"]["combinaisons"]:
                    session.merge(...)
            if course and is_arrivee_definitive(course):
                set_course_is_over(data["course_id"], session)
                rapports = get_rapports_definitifs(data["course_id"])  # ou inclus dans fetch
                ...
        session.commit()
```

**Note** : on peut aussi paralléliser `get_rapports_definitifs` dans la phase fetch si `is_arrivee_definitive(course)` est True.

#### `scrap_programmes` — N dates en parallèle

```python
def fetch_programme(date_str: str):
    programme = get_programme(ProgrammeIdentifier(date_str))
    return date_str, programme

with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(fetch_programme, programmes_disponibles)

with get_session() as session:
    for date_str, programme in results:
        if programme:
            session.merge(Programme.model_validate(
                ProgrammeCreate(id=date_str, raw=programme)
            ))
    session.commit()
```

#### `scrap_courses` — parallélisme limité

Par programme, la structure est hiérarchique (réunions → courses). Paralléliser **à l'intérieur d'un programme** est possible (fetch déjà fait en 1 appel). Le gain vient surtout du **batch commit** (cf. §12.6), pas du multithreading.

#### `historize` — parallélisme avec prudence

```python
# historize.py — aujourd'hui
for programme in programmes:
    scrap_past_programmes(programme)   # 1 HTTP + 1 commit par jour → très long sur 10 ans
```

Pour 3650 jours × 300ms = **~18 minutes** séquentiel.

Avec 10 threads : **~2 minutes**. Mais risque de surcharge API PMU → `max_workers=5` + rate limit recommandé.

---

### 14.7 Alternative — asyncio + httpx (refactor plus profond)

Si vous migrez le client PMU vers async :

```python
# pmu/client_async.py
import httpx

async def fetch_pmu_api(url: str) -> dict | None:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{BASE_URL}/{url}")
        ...

# scraper/pipelines/scrap_participants_async.py
import asyncio

async def scrap_participants():
    course_ids = ...
    results = await asyncio.gather(*[
        fetch_participants_async(cid) for cid in course_ids
    ], return_exceptions=True)
    # write séquentiel ensuite
```

| Approche                          | Effort     | Gain I/O   | Complexité DB             |
| --------------------------------- | ---------- | ---------- | ------------------------- |
| `ThreadPoolExecutor` + `requests` | **Faible** | Élevé      | Faible (write séquentiel) |
| `asyncio` + `httpx`               | Élevé      | Élevé      | Moyenne                   |
| Celery tasks (1 course = 1 task)  | Élevé      | Très élevé | Élevée (orchestration)    |

**Recommandation** : commencer par `ThreadPoolExecutor` — changement minimal, gros gain.

---

### 14.8 Limitation du parallélisme — rate limiting PMU

```python
# utils/rate_limit.py
import threading
import time

class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.lock = threading.Lock()
        self.calls = []

    def acquire(self):
        with self.lock:
            now = time.time()
            self.calls = [t for t in self.calls if now - t < self.period]
            if len(self.calls) >= self.max_calls:
                time.sleep(self.period - (now - self.calls[0]))
            self.calls.append(time.time())

pmu_limiter = RateLimiter(max_calls=10, period=1.0)  # 10 req/s max

def fetch_pmu_api(url: str) -> dict | None:
    pmu_limiter.acquire()
    ...
```

Sans rate limiter, 20 threads simultanés peuvent provoquer des 503 → le retry cassé actuel aggrave le problème.

---

### 14.9 Parallélisme inter-pipelines (orchestrateur)

#### Aujourd'hui

```python
def every_day():
    scrap_programmes()      # ~5s
    scrap_courses()         # ~30s
    scrap_participants()    # ~22s
    # Total : ~57s séquentiel
```

#### Option A — paralléliser les pipelines indépendants (déconseillé)

`scrap_courses` dépend des programmes scrapés → **ordre obligatoire** :

1. `scrap_programmes`
2. `scrap_courses`
3. `scrap_participants`

On ne peut pas paralléliser ces 3 étapes entre elles sans risque de données manquantes.

#### Option B — paralléliser à l'intérieur de chaque pipeline (recommandé)

```
every_day():
  scrap_programmes()     ← threads sur les dates
  scrap_courses()        ← batch commit
  scrap_participants()   ← threads sur les courses  ✅ plus gros gain
```

#### Option C — séparer `scrap_bet` du reste (déjà le cas)

`every_five_minutes()` est indépendant → peut tourner dans un **processus worker séparé** sans bloquer `every_day()`.

---

### 14.10 Estimation des gains par pipeline

Hypothèses : 40 courses actives, 12 participants/course, 300ms HTTP, 20ms DB/write, 8 threads.

| Pipeline             | Durée actuelle (estim.)    | Avec threads (8) + batch DB | Gain |
| -------------------- | -------------------------- | --------------------------- | ---- |
| `scrap_programmes`   | ~5s (15 dates)             | ~1s                         | ×5   |
| `scrap_courses`      | ~30s (commits N×)          | ~8s (batch commit surtout)  | ×3-4 |
| `scrap_participants` | ~22s                       | ~3-4s                       | ×5-7 |
| `scrap_bet`          | ~60s (3 HTTP × 40 courses) | ~10-15s                     | ×4-6 |
| `historize` (1 an)   | ~110s (365 jours)          | ~15-20s                     | ×5-7 |

**Le gain réel dépend** de la latence PMU, du nombre de courses actives, et du rate limiting appliqué.

---

### 14.11 Plan de mise en place recommandé

#### Étape 1 — Prérequis (P0 audit)

- [ ] Fix retry + timeout `fetch_pmu_api`
- [ ] Guards `None` dans les pipelines
- [ ] Batch commit (§12.6) — gain immédiat sans threads

#### Étape 2 — Multithreading fetch (1-2 jours)

- [ ] Extraire fonctions `fetch_*` pures (sans session DB)
- [ ] Appliquer `ThreadPoolExecutor` sur `scrap_participants` (meilleur ROI)
- [ ] Puis `scrap_bet`, puis `scrap_programmes`
- [ ] Ajouter rate limiter PMU
- [ ] `MAX_WORKERS` configurable via env (`SCRAPER_MAX_WORKERS=8`)

#### Étape 3 — Isolation (1 semaine)

- [ ] Worker scraper séparé de l'API (§13.5 niveau 3)
- [ ] Un seul processus exécute les crons → pas de concurrence accidentelle
- [ ] L'API reste responsive quel que soit le chargement scraper

#### Étape 4 — Optionnel

- [ ] Migration `httpx` async si besoin de plus de contrôle
- [ ] Queue Celery/ARQ pour historize massif (milliers de jours)

---

### 14.12 Exemple de configuration `.env`

```bash
# Parallélisme scraper
SCRAPER_MAX_WORKERS=8          # threads pour fetch PMU
SCRAPER_RATE_LIMIT=10          # requêtes max par seconde vers PMU

# Serveur HTTP
UVICORN_WORKERS=2              # processus API (sans scrapers au startup)
RUN_SCRAPERS_ON_STARTUP=false  # ne pas scraper au boot
```

```bash
# Lancement recommandé
# Terminal 1 — API seule
uvicorn server:app --host 0.0.0.0 --port 8080 --workers 2

# Terminal 2 — worker scraper
python -m scraper.worker   # à créer : exécute repeat_every / repeat_at
```

---

### 14.13 Synthèse parallélisme

| Question                                                | Réponse                                                     |
| ------------------------------------------------------- | ----------------------------------------------------------- |
| Le server traite plusieurs requêtes HTTP en parallèle ? | **Partiellement** — routes courtes OK, scraping bloque tout |
| Les pipelines parallélisent les appels PMU ?            | **Non** — tout est séquentiel                               |
| Première action la plus rentable ?                      | Retirer scraping de `/` + BackgroundTasks pour jobs longs   |
| Plus gros gain perf pipelines ?                         | `ThreadPoolExecutor` sur fetch HTTP + batch DB commit       |
| Risque principal ?                                      | Rate limit PMU + sessions DB partagées entre threads        |
| Architecture cible ?                                    | API (multi-workers) + worker scraper (threads) séparés      |

---

_Audit réalisé par analyse statique (ruff) et revue manuelle du code source._
