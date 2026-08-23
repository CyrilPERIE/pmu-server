from api.routes import metrics
from fastapi import FastAPI
from utils.logger import setup_logging
import uvicorn
from scraper.orchestrator import every_day, every_five_minutes
from fastapi_utilities import repeat_every, repeat_at


app = FastAPI()

app.include_router(metrics.router)
# app.include_router(scrap.router)

@app.on_event('startup')
def startup_event():
    setup_logging()
    every_day()

@app.on_event('startup')
@repeat_every(seconds=60 * 5)
def every_five_minutes_event():
    every_five_minutes()

## Tous les jours à 4h
@app.on_event('startup')
@repeat_at(cron='0 4 * * *')
def every_day_event():
    every_day()

'''TODO: Création d'un middleware pour éviter le DDOS.
'''
'''TODO: Permettre le multi-threading pour la gestion asyncronne des requêtes et des pipelines.
'''
@app.get("/health")
async def read_root():
    return {"message": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)