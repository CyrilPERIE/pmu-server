from fastapi import APIRouter

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/")
def get_metrics():
    return {"message": "Metrics!"}