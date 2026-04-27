import backend.app.models  # noqa: F401
from backend.app.core.database import Base, engine
from backend.app.core.schema_sync import sync_item_columns


def init_db():
    Base.metadata.create_all(bind=engine)
    sync_item_columns(engine)
    print("数据库初始化完成")


if __name__ == "__main__":
    init_db()
