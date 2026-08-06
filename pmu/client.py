import logging
from requests import get

BASE_URL = "https://online.turfinfo.api.pmu.fr/rest/client/61/programme"
MAX_RETRIES = 3
MIN_DATE = "01012016"

logger = logging.getLogger(__name__)

def fetch_pmu_api(url: str) -> dict | None:
    for _ in range(MAX_RETRIES):
        logger.info(f"Fetching data from {BASE_URL}/{url}")
        response = get(f"{BASE_URL}/{url}")
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch data from {url}: {response.status_code}")
            return None
    raise Exception(f"Failed to fetch data from {url}")