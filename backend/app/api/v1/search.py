from fastapi import APIRouter

router = APIRouter()

@router.get("/ping")
def search_ping():
    return {"module": "search", "status": "ok"}
