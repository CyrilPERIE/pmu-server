import sys
from api.routes import metrics
from api.routes import scrap
from fastapi import FastAPI
from utils.logger import setup_logging
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from scraper.orchestrator import every_day, every_five_minutes

pass_scraper = False

app = FastAPI()

app.include_router(metrics.router)
app.include_router(scrap.router)

scheduler = BackgroundScheduler()

@app.on_event('startup')
def startup_event():
    setup_logging()
    if not pass_scraper:
        # Scraping tasks are long-running and must never block application
        # startup, otherwise Railway's ingress will time out waiting for the
        # HTTP server to come up and requests will fail with 502.
        # Run once shortly after startup, then on a schedule (every day at
        # 4am, and every 5 minutes), all in the background.
        scheduler.add_job(every_day, 'date')
        scheduler.add_job(every_five_minutes, 'date')
        scheduler.add_job(every_day, 'cron', hour=4)
        scheduler.add_job(every_five_minutes, 'interval', minutes=5)
        scheduler.start()

@app.on_event('shutdown')
def shutdown_event():
    if scheduler.running:
        scheduler.shutdown(wait=False)

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
