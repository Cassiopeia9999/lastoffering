from fastapi import APIRouter

from backend.app.api.v1 import user, item, search, notify, message, match, admin

api_router = APIRouter()

api_router.include_router(user.router)
api_router.include_router(item.router)
api_router.include_router(search.router)
api_router.include_router(notify.router)
api_router.include_router(message.router)
api_router.include_router(match.router)
api_router.include_router(admin.router)

# AI 扩展接口依赖 PyTorch 模型、本地 NLP 组件及可选的大模型配置，导入失败时跳过，不影响主流程
try:
    from backend.app.api.v1 import ai
    api_router.include_router(ai.router, prefix="/ai", tags=["AI扩展模块"])
except Exception as e:
    import warnings
    warnings.warn(f"AI 扩展模块未加载（需相关依赖与模型文件）: {e}", UserWarning)
