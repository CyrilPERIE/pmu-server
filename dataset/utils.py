"""Socle commun aux chargeurs de datasets.

Toutes les entités portent la date du programme dans les 8 premiers caractères de
leur identifiant (`DDMMYYYY`, puis `/R{n}`, `/C{n}`, `/P{n}`...). C'est donc ce
préfixe qui sert de filtre temporel commun, sans jointure.
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from pmu.types.types import ProgrammeIdentifier
from pmu.utils import programme_date_to_date
from service.utils.deps import engine

PROGRAMME_DATE = "to_date(substring(id, 1, 8), 'DDMMYYYY')"
DATE_WINDOW = f"{PROGRAMME_DATE} between :start_date and :end_date"


def load_sql(
    query: str,
    start_date: ProgrammeIdentifier,
    end_date: ProgrammeIdentifier,
    **extra_params: object,
) -> pd.DataFrame:
    """Exécute une requête paramétrée par `:start_date` et `:end_date`."""
    params = {
        "start_date": programme_date_to_date(str(start_date)).date(),
        "end_date": programme_date_to_date(str(end_date)).date(),
        **extra_params,
    }
    with engine.connect() as connection:
        return pd.read_sql(text(query), connection, params=params)


def load_query(query: str, **params: object) -> pd.DataFrame:
    """Exécute une requête SQL libre, sans fenêtre de dates."""
    with engine.connect() as connection:
        return pd.read_sql(text(query), connection, params=params or None)
