import logging
import random
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter

BASE_URL = "https://online.turfinfo.api.pmu.fr/rest/client/61/programme"

MAX_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 0.5
BACKOFF_MAX_SECONDS = 8.0
TIMEOUT = (5, 15)  # (connect, read)
RETRYABLE_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})

logger = logging.getLogger(__name__)


class PmuApiError(RuntimeError):
    """Échec définitif d'un appel à l'API PMU."""

    def __init__(self, url: str, *, status_code: int | None, attempts: int) -> None:
        self.url = url
        self.status_code = status_code
        self.attempts = attempts
        super().__init__(
            f"Échec de {url} après {attempts} tentative(s) (status={status_code})"
        )


_session = requests.Session()
_session.mount("https://", HTTPAdapter(pool_maxsize=10))


def _backoff_delay(attempt: int, retry_after: str | None) -> float:
    if retry_after and retry_after.isdigit():
        return min(float(retry_after), BACKOFF_MAX_SECONDS)
    delay = min(BACKOFF_BASE_SECONDS * 2**attempt, BACKOFF_MAX_SECONDS)
    return delay * (0.5 + random.random() / 2)


'''
TODO-1: Ajouter un type de données T en entrée (pydantic)
TODO-2: Tester le type de données T en sortie pour valider la donnée renvoyée par l'API PMU(pydantic)
'''
def fetch_pmu_api(path: str) -> dict[str, Any] | None:
    """Récupère une ressource de l'API PMU.

    Args:
        path: chemin relatif à BASE_URL, ex. "12032019/R1/C3/participants".

    Returns:
        Le corps JSON décodé, ou None si la ressource n'existe pas (404).

    Raises:
        PmuApiError: erreur non réessayable, ou échec après MAX_ATTEMPTS.
    """
    url = f"{BASE_URL}/{path}"
    last_status: int | None = None

    for attempt in range(MAX_ATTEMPTS):
        retry_after: str | None = None
        try:
            logger.info(f"GET {url} (tentative {attempt + 1}/{MAX_ATTEMPTS})")
            response = _session.get(url, timeout=TIMEOUT)
        except requests.RequestException as exc:
            last_status = None
            logger.warning(f"Erreur réseau sur {url} : {exc}")
        else:
            last_status = response.status_code
            if response.status_code == 404:
                logger.info(f"Aucune donnée pour {url}")
                return None
            if response.ok:
                try:
                    return response.json()
                except ValueError:
                    logger.warning(f"Réponse 200 non-JSON sur {url}")
            elif response.status_code not in RETRYABLE_STATUS:
                raise PmuApiError(
                    url, status_code=response.status_code, attempts=attempt + 1
                )
            else:
                retry_after = response.headers.get("Retry-After")
                logger.warning(f"Statut {response.status_code} sur {url}")

        if attempt < MAX_ATTEMPTS - 1:
            time.sleep(_backoff_delay(attempt, retry_after))

    raise PmuApiError(url=url, status_code=last_status, attempts=MAX_ATTEMPTS)