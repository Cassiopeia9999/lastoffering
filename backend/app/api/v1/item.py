from fastapi import APIRouter

router = APIRouter()

@router.get("/ping")
def item_ping():
    return {"module": "item", "status": "ok"}
