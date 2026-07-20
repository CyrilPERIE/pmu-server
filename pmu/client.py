import logging
from requests import get

BASE_URL = "https://online.turfinfo.api.pmu.fr/rest/client/61/programme"
MAX_RETRIES = 3
MIN_DATE = "01012016"

logger = logging.getLogger("pmu.client")

def fetch_pmu_api(url: str) -> dict:
    for _ in range(MAX_RETRIES):
        logger.info(f"Fetching data from {url}")
        print(f"{BASE_URL}/{url}")
        response = get(f"{BASE_URL}/{url}")
        return response
    raise Exception(f"Failed to fetch data from {url}")