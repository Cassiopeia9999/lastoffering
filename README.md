# 校园失物招领智能管理系统

一个面向校园场景的失物招领 Web 系统，支持失物/招领信息发布、图片分类、以图搜物、自然语言智能寻物、快速发布、异步智能匹配、站内通知、留言沟通和管理员后台管理。

## 项目特点

- 前后端分离：`Vue 3 + Vite + Element Plus` 与 `FastAPI + SQLAlchemy + MySQL`
- 图像智能：支持图片分类、特征提取、相似物品检索
- 语义智能：支持自然语言寻物和自然语言快速发布
- 智能匹配：结合图像、颜色、品牌、关键词进行综合评分并异步推送通知
- 管理后台：支持用户管理、物品审核、系统统计

## 技术栈

- 前端：Vue 3、Vite、Vue Router、Pinia、Element Plus、Axios
- 后端：FastAPI、Uvicorn、SQLAlchemy、Pydantic、PyMySQL
- 数据库：MySQL 8
- AI：
  - 本地视觉模型：EfficientNet-B0 思路的分类与特征提取
  - 语义增强：ARK 大模型接口 + 本地语义归一化规则
- 部署：Docker Compose、Nginx

## 核心功能

- 用户注册、登录、JWT 认证、个人资料管理、头像上传
- 失物/招领信息发布、编辑、下架、恢复、关闭
- 图片上传、图片裁剪、AI 分类建议
- 以图搜物
- 智能寻物：根据自然语言描述提取条件并检索
- 快速发布：根据自然语言描述自动整理表单字段
- 相似物品推荐
- 留言与通知
- 疑似遗失匹配、确认匹配、完成认领
- 管理员用户管理、物品管理、统计看板

## 项目结构

```text
items/
├─ ai_module/                  # AI 训练与推理脚本、模型、数据集目录
├─ backend/                    # FastAPI 后端
│  ├─ app/
│  │  ├─ api/v1/               # API 路由
│  │  ├─ core/                 # 配置、数据库、认证依赖
│  │  ├─ crud/                 # 数据访问层
│  │  ├─ models/               # ORM 模型
│  │  ├─ schemas/              # 请求/响应模型
│  │  ├─ services/             # AI、匹配、语义处理等服务
│  │  └─ utils/                # 文件工具等
│  └─ scripts/                 # 数据回填、联调测试脚本
├─ dataset/                    # 数据集处理辅助目录
├─ docker/                     # Dockerfile 与 Nginx 配置
├─ docs/                       # 设计文档与补充说明
├─ frontend/                   # Vue 前端
├─ media/                      # 上传媒体文件
├─ docker-compose.yml
├─ requirements.txt
└─ requirements-minimal.txt
```

## 快速开始

### 1. 配置环境变量

将 [`.env.example`](F:/Last_offering/items/.env.example) 复制为 `.env`，按实际环境填写数据库与密钥配置。

### 2. 启动 MySQL

创建数据库：

```sql
CREATE DATABASE IF NOT EXISTS lostfound CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 启动后端

```bash
cd F:\Last_offering\items
pip install -r requirements-minimal.txt
python backend/init_db.py
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 启动前端

```bash
cd F:\Last_offering\items\frontend
npm install
npm run dev
```

### 5. 访问系统

- 前端：`http://localhost:5173`
- 后端文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`

## Docker 部署

项目提供了 `docker-compose.yml`，可直接启动 `mysql + backend + frontend`：

```bash
docker compose up --build
```

启动后默认访问：

- 前端：`http://localhost`
- 后端 API：`http://localhost/api/v1`

## 相关文档

- [系统详细设计文档](F:/Last_offering/items/系统详细设计文档.md)
- [系统使用文档](F:/Last_offering/items/系统使用文档.md)
- [环境安装书](F:/Last_offering/items/环境安装书.md)

## 测试与辅助脚本

- [test_api.py](F:/Last_offering/items/test_api.py)：基础接口联调脚本
- [test_ai.py](F:/Last_offering/items/test_ai.py)：AI 检索联调脚本
- [backfill_item_features.py](F:/Last_offering/items/backend/scripts/backfill_item_features.py)：历史物品字段补全脚本

## 当前说明

- 当前代码中部分前端头像/图片地址拼接仍默认使用 `localhost:8000`，部署到其他主机时建议统一调整为基于配置的资源地址。
- 旧工作日志与当前实现存在少量阶段性差异，使用和答辩时建议以当前代码与文档为准。

## License

本项目当前主要用于毕业设计与学习交流，如需对外开源发布，建议后续补充正式 License。
