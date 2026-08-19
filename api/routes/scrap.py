from fastapi import APIRouter, BackgroundTasks
from pmu.types.types import ProgrammeIdentifier
from scraper.pipelines.recuperation.historize import historize as run_historize, HIGHEST_DATE, LOWEST_DATE
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scrap", tags=["scrap"])

@router.get("/historize")
def historize(background_tasks: BackgroundTasks, start_date: str | None = None, end_date: str | None = None) -> dict[str, str]:
    start = LOWEST_DATE
    end = HIGHEST_DATE
    if start_date and type(start_date) == str and start_date.isdigit() and len(start_date) == 8:
        start = ProgrammeIdentifier(start_date)
    if end_date and type(end_date) == str and end_date.isdigit() and len(end_date) == 8:
        end = ProgrammeIdentifier(end_date)
    background_tasks.add_task(run_historize, start, end)
    return {"message": "Historization started"}