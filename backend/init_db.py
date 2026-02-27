from backend.app.core.database import Base, engine
from backend.app.models import user  # 导入所有模型

def init_db():
    Base.metadata.create_all(bind=engine)
    print("数据库初始化完成")

if __name__ == "__main__":
    init_db()
