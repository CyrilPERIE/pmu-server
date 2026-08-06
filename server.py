from api.routes import metrics
from fastapi import FastAPI
from scraper.pipelines.scrap_programmes import scrap_programmes
import uvicorn
from scraper.orchestrator import every_midnight, every_five_minutes
from fastapi_utilities import repeat_every, repeat_at


app = FastAPI()

app.include_router(metrics.router)

@app.on_event('startup')
@repeat_every(seconds=60 * 5)
def every_five_minutes_task():
    every_five_minutes()

@app.on_event('startup')
@repeat_at(cron='0 0 * * *')
def every_midnight_task():
    every_midnight()


@app.on_event('startup')
def startup_event():
    every_midnight()
    every_five_minutes()

@app.get("/")
async def read_root():
    return scrap_programmes()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)