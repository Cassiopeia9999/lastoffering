from backend.app.core.database import Base, engine
import backend.app.models  # 导入所有模型，确保表被创建

def init_db():
    Base.metadata.create_all(bind=engine)
    print("数据库初始化完成")

if __name__ == "__main__":
    init_db()
