from datetime import datetime
from fastapi import FastAPI
from pmu.endpoints import get_pronostics
from pmu.mock.generate import generate_mock_data
from pmu.types.types import CourseIdentifier
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)