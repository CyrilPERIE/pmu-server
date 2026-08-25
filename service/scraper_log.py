from models.scraper_log import ScraperLogCreate, ScraperLog, ScraperStatus
from sqlmodel import Session, select
from service.utils.crud import upsert

def create_scraper_log(scraper_log_create: ScraperLogCreate, session: Session) -> ScraperLog:
    with session:
        scraper_log = ScraperLog(
            scraper=scraper_log_create.scraper
        )
        session.add(scraper_log)
        session.commit()
        session.refresh(scraper_log)
    return scraper_log

def update_scraper_log(scraper_log: ScraperLog,session: Session) -> ScraperLog:
    return upsert(ScraperLog, scraper_log, session)

def get_scraper_logs(session: Session, limit: int = 15, offset: int = 0) -> list[ScraperLog]:
    return session.exec(select(ScraperLog).limit(limit).offset(offset)).all()