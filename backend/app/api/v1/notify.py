from fastapi import APIRouter

router = APIRouter()

@router.get("/ping")
def notify_ping():
    return {"module": "notify", "status": "ok"}
