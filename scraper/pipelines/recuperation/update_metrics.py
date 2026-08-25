from service.metrics import *
from service.utils.deps import get_session
from scraper.pipelines.utils.pipeline_decorator import log_scraper

@log_scraper
def update_metrics() -> None:
    with get_session() as session:
        update_count_courses(session)
        update_count_reunions(session)
        update_count_programmes(session)
        update_count_courses_over(session)
        update_count_courses_incoming(session)
        update_count_mean_courses_by_programme(session)
        update_count_mean_reunions_by_programme(session)
        update_lowest_year_programme(session)