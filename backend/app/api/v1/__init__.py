from fastapi import APIRouter

from backend.app.api.v1 import user, item, search, notify, message, match

api_router = APIRouter()

api_router.include_router(user.router)
api_router.include_router(item.router)
api_router.include_router(search.router)
api_router.include_router(notify.router)
api_router.include_router(message.router)
api_router.include_router(match.router)
