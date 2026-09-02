import sys
from api.routes import metrics
from api.routes import scrap
from fastapi import FastAPI
from utils.logger import setup_logging
import uvicorn
from scraper.orchestrator import every_day, every_five_minutes

pass_scraper = False

app = FastAPI()

app.include_router(metrics.router)
app.include_router(scrap.router)

@app.on_event('startup')
def startup_event():
    setup_logging()
    if not pass_scraper:
        every_day()

@app.on_event('startup')
def every_five_minutes_event():
    if not pass_scraper:
        every_five_minutes()

## Tous les jours à 4h
@app.on_event('startup')
def every_day_event():
    if not pass_scraper:
        every_day()

'''TODO: Création d'un middleware pour éviter le DDOS.
'''
'''TODO: Permettre le multi-threading pour la gestion asyncronne des requêtes et des pipelines.
'''
@app.get("/health")
async def read_root():
    return {"message": "ok"}


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--pass-scraper" in args:
        pass_scraper = True
    uvicorn.run(app, host="0.0.0.0", port=8080)
