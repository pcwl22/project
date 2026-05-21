# ShelfDetect

基于 YOLOv8 的货架商品检测与空货架识别系统，提供图片检测、视频检测、摄像头实时检测、历史记录管理、模型管理、用户管理和算法参数配置等功能。

## 功能特性

- 图片检测：上传单张图片并返回标注结果、空货架数量和占比统计
- 视频检测：上传视频并输出处理后的视频结果
- 摄像头检测：实时分析摄像头画面并统计空货架情况
- 历史记录：保存检测结果，支持查看详情与删除记录
- 模型管理：查看可用模型并上传新的 `.pt` 权重文件
- 用户管理：支持登录、找回密码和管理员权限控制
- 参数配置：可在线调整置信度、IOU 和空货架检测相关参数

## 技术栈

- 后端：FastAPI、SQLAlchemy、PyMySQL
- 前端：Vue 3、TypeScript、Vite、Element Plus
- 检测模型：Ultralytics YOLOv8
- 数据库：MySQL

## 项目结构

```text
project/
├─ backend/                # FastAPI 后端
│  └─ app/
│     ├─ routes/           # 认证、检测、配置、管理接口
│     ├─ services/         # YOLO 检测服务
│     ├─ config.py         # 后端配置
│     ├─ db.py             # 数据库连接
│     └─ main.py           # 后端入口
├─ frontend/               # Vue 前端
│  └─ src/components/      # 功能页面组件
├─ start.py                # 一键启动脚本
├─ init_directories.py     # 初始化输出目录
├─ manage_database.py      # 数据库管理脚本
├─ update_database.py      # 数据库更新脚本
├─ algorithm_config.json   # 算法配置持久化文件
└─ yolov8n.pt              # 示例模型文件
```

## 运行环境

- Python 3.9+
- Node.js 18+
- MySQL 8.0+
- 已安装 YOLOv8 相关 Python 依赖

## 后端配置

后端默认从环境变量读取配置，也内置了本地开发默认值。关键配置位于 `backend/app/config.py`：

- `DATABASE_URL`：MySQL 连接串
- `YOLO_WEIGHTS`：默认模型路径
- `MODEL_DIR`：模型目录
- `OUTPUT_DIR`：检测结果输出目录

如果直接在其他机器运行，建议优先通过环境变量覆盖这些本地绝对路径。

## 安装与启动

### 1. 安装后端依赖

根据你的环境安装至少以下依赖：

```bash
pip install fastapi uvicorn sqlalchemy pymysql ultralytics python-multipart
```

如需视频和图像处理，还需要确保本地已安装 OpenCV 等相关依赖。

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 初始化目录

```bash
python init_directories.py
```

### 4. 启动后端

在项目根目录执行：

```bash
uvicorn backend.app.main:app --reload --port 8000
```

### 5. 启动前端

```bash
cd frontend
npm run dev
```

### 6. 或使用一键启动脚本

```bash
python start.py
```

默认访问地址：

- 前端：[http://localhost:5173](http://localhost:5173)
- 后端 API：[http://localhost:8000](http://localhost:8000)
- API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)

## 主要接口

- `POST /api/detect`：图片、视频、摄像头检测
- `GET /api/models`：获取可用模型列表
- `POST /api/upload_model`：上传模型文件
- `GET /api/detections/`：获取历史记录
- `GET /api/detections/{record_id}`：获取检测详情
- `DELETE /api/detections/{record_id}`：删除检测记录
- `GET /api/config/detection`：获取算法配置
- `PUT /api/config/detection`：更新算法配置
- `PUT /api/config/thresholds`：更新检测阈值

## 当前注意事项

- 仓库中存在较多面向本机环境的绝对路径，跨机器部署前需要先调整配置
- 数据库默认配置写的是本地 MySQL，首次运行前需要确认账号、密码和库名
- 根目录还有一个旧的 `main.py`，当前实际使用的后端入口是 `backend/app/main.py`

## 适用场景

- 超市货架缺货监测
- 商品陈列状态巡检
- 零售场景的视频智能分析

