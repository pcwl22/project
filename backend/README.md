# 后端目录

基于 FastAPI 的后端服务，提供 RESTful API 接口。

## 技术栈
- **FastAPI**: 现代化的 Python Web 框架
- **SQLAlchemy**: ORM 框架
- **PyMySQL**: MySQL 数据库驱动
- **Uvicorn**: ASGI 服务器
- **Pydantic**: 数据验证
- **Ultralytics**: YOLOv8 实现

## 目录结构

```
backend/
└── app/
    ├── routes/              # API 路由
    │   ├── auth.py         # 认证接口
    │   └── detections.py   # 检测接口
    ├── services/            # 业务逻辑
    │   └── yolo_service.py # YOLO 检测服务
    ├── models.py            # 数据库模型
    ├── schemas.py           # 数据验证模式
    ├── config.py            # 配置文件
    ├── db.py               # 数据库连接
    └── main.py             # 应用入口
```

## 主要模块

### 1. main.py
应用程序入口，配置 CORS、路由注册、静态文件服务。

### 2. config.py
系统配置：
- 数据库连接字符串
- YOLO 模型路径
- 输出目录路径

### 3. db.py
数据库连接管理：
- SQLAlchemy 引擎配置
- 会话管理
- 依赖注入

### 4. models.py
数据库模型定义：
- User（用户）
- DetectionResult（检测记录）
- DetectionBox（检测框）

### 5. schemas.py
Pydantic 数据验证模式，定义 API 请求/响应格式。

## API 接口

### 认证接口 (/api/auth)
```python
POST /api/auth/login      # 用户登录
POST /api/auth/register   # 用户注册
```

### 检测接口
```python
POST /upload_model        # 上传模型
POST /detect              # 图片检测
GET  /detections/         # 获取历史列表
GET  /detections/{id}     # 获取记录详情
DELETE /detections/{id}   # 删除记录
GET  /detections/{id}/original   # 获取原图
GET  /detections/{id}/annotated  # 获取标注图
```

## 启动方式

### 开发模式
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 生产模式
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 使用启动脚本
```bash
cd project
python start.py
```

## 配置说明

### 数据库配置 (config.py)
```python
database_url = "mysql+pymysql://root:202217@localhost:3306/ultralytics_auth"
```

### 模型路径配置
```python
yolo_weights = r"E:\bysj\ultralytics-8.2.27\runs\detect\best.pt"
```

### 输出目录配置
```python
output_dir = r"E:\bysj\ultralytics-8.2.27\test\api"
```

## 数据库模型

### User（用户表）
- id: 主键
- username: 用户名（唯一）
- password: 密码
- created_at: 创建时间

### DetectionResult（检测记录表）
- id: 主键
- image_path: 原始图片路径
- saved_image_path: 标注图片路径
- created_at: 创建时间
- user_id: 用户ID

### DetectionBox（检测框表）
- id: 主键
- result_id: 关联的检测记录ID
- cls_name: 类别名称
- x1, y1, x2, y2: 检测框坐标
- score: 置信度
- extra: 额外信息

## 业务逻辑

### YOLO 检测服务 (yolo_service.py)
核心功能：
1. 加载 YOLO 模型
2. 图片预处理
3. 目标检测
4. 空货架推算
5. 结果标注
6. 图片保存

检测流程：
```
上传图片 → 模型推理 → 商品检测 → 空位推算 → 绘制标注 → 保存结果 → 返回数据
```

## 依赖管理

### 主要依赖
```
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
pymysql>=1.1.0
pydantic>=2.0.0
ultralytics>=8.0.0
opencv-python>=4.8.0
pillow>=10.0.0
python-multipart>=0.0.6
```

### 安装依赖
```bash
pip install -r requirements.txt
```

## 开发指南

### 添加新接口
1. 在 `routes/` 目录创建路由文件
2. 定义路由和处理函数
3. 在 `main.py` 中注册路由

示例：
```python
# routes/new_feature.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/feature", tags=["feature"])

@router.get("/")
def get_feature():
    return {"message": "Hello"}

# main.py
from .routes.new_feature import router as feature_router
app.include_router(feature_router)
```

### 添加数据库模型
1. 在 `models.py` 中定义模型类
2. 继承 `Base` 类
3. 定义表名和字段
4. 运行应用自动创建表

### 添加业务逻辑
1. 在 `services/` 目录创建服务文件
2. 定义服务类和方法
3. 在路由中调用服务

## 错误处理

### HTTP 异常
```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="记录不存在")
```

### 数据库异常
```python
try:
    db.commit()
except Exception as e:
    db.rollback()
    raise HTTPException(status_code=500, detail=str(e))
```

## 日志记录

使用 Python logging 模块：
```python
import logging

logger = logging.getLogger(__name__)
logger.info("检测完成")
logger.error("检测失败", exc_info=True)
```

## 性能优化

### 1. 数据库连接池
SQLAlchemy 自动管理连接池

### 2. 异步处理
FastAPI 支持异步路由：
```python
@router.get("/")
async def get_data():
    return await fetch_data()
```

### 3. 缓存
使用 Redis 或内存缓存热点数据

### 4. 批量操作
使用 SQLAlchemy 批量插入/更新

## 安全性

### 1. 密码加密
使用 hashlib 或 bcrypt 加密密码

### 2. SQL 注入防护
使用 ORM 参数化查询

### 3. CORS 配置
限制允许的源：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5176"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. 输入验证
使用 Pydantic 模型验证所有输入

## 测试

### 单元测试
```bash
pytest tests/
```

### API 测试
访问 http://localhost:8000/docs 使用 Swagger UI 测试

## 部署

### Docker 部署
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 生产环境配置
- 使用环境变量管理配置
- 启用 HTTPS
- 配置反向代理（Nginx）
- 使用进程管理器（Supervisor/systemd）

## 监控

### 健康检查
```python
@app.get("/health")
def health_check():
    return {"status": "ok"}
```

### 性能监控
- 使用 Prometheus + Grafana
- 记录 API 响应时间
- 监控数据库连接数

## 常见问题

### Q1: 数据库连接失败
A: 检查 MySQL 服务是否运行，配置是否正确

### Q2: 模型加载失败
A: 检查模型文件路径，确保文件存在

### Q3: CORS 错误
A: 检查 CORS 中间件配置，确保允许前端域名

### Q4: 文件上传失败
A: 检查文件大小限制，确保目录有写权限

## 参考资料

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Ultralytics 文档](https://docs.ultralytics.com/)
