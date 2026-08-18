import datetime
from pmu.types.types import ProgrammeIdentifier
from pmu.utils import date_to_programme_date
from scraper.pipelines.recuperation.scrap_past_programmes import scrap_past_programmes

LOWEST_DATE = ProgrammeIdentifier("01012014")
HIGHEST_DATE = ProgrammeIdentifier(date_to_programme_date(datetime.date.today()))

'''
Démarre une collecte qui peut avoir des dates antérieures à aujourd'hui.
'''
def historize(start_date: ProgrammeIdentifier = LOWEST_DATE, end_date: ProgrammeIdentifier = HIGHEST_DATE) -> None:
    if start_date < LOWEST_DATE:
        start_date = LOWEST_DATE
    if end_date > HIGHEST_DATE:
        end_date = HIGHEST_DATE
    if start_date > end_date:
        raise ValueError("start_date must be before end_date")
    programmes: list[ProgrammeIdentifier] = []
    while start_date <= end_date:
        programmes.append(start_date)
        start_date = start_date.increment()
    for programme in programmes:
        scrap_past_programmes(programme)
    # scrap_courses.scrap_courses()
    # scrap_participants.scrap_participants()
    # scrap_bet.scrap_bet()