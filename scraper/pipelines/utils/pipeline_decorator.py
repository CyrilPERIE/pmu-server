from datetime import datetime
from models.scraper_log import ScraperLogCreate, ScraperStatus
from service.scraper_log import create_scraper_log, update_scraper_log
from service.utils.deps import get_session
from functools import wraps

def log_scraper(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        with get_session() as session:
            scraper_log = create_scraper_log(
                ScraperLogCreate(scraper=func.__name__),
                session,
            )

            try:
                result = func(*args, **kwargs)
                
                scraper_log.end_time = datetime.now()
                scraper_log.status = ScraperStatus.COMPLETED
                update_scraper_log(
                    scraper_log,
                    session
                )

                return result

            except Exception:
                scraper_log.end_time = datetime.now()
                scraper_log.status = ScraperStatus.FAILED
                update_scraper_log(
                    scraper_log,
                    session
                )
                raise

    return wrapper