# ShelfDetect

基于 YOLOv8 的货架商品检测与空货架识别系统，面向超市、便利店和仓储货架巡检场景，支持图片检测、视频检测、摄像头实时检测、历史记录管理、模型管理、用户管理和算法参数配置。

## 项目概述

传统货架巡检依赖人工观察，存在效率低、主观性强、响应慢的问题。本项目以 YOLOv8 目标检测模型为核心，结合货架场景下的空货架推断逻辑，构建了一套前后端分离的智能巡检系统，实现对商品陈列状态和空货位情况的自动识别、统计与可视化展示。

项目不仅关注模型推理本身，还完成了从检测能力到业务系统落地的完整闭环，包括：

- 多输入检测：支持图片、视频、摄像头三种检测模式
- 空货架分析：统计空货架数量、总货位数量和空置比例
- 检测记录管理：支持历史记录保存、查询和删除
- 模型管理：支持模型切换与 `.pt` 权重上传
- 参数配置：支持在线调整置信度、IOU 和空货架检测参数
- 用户与权限：支持登录、找回密码和管理员权限控制

## 核心价值

- 降本增效：降低人工巡检成本，提高补货与盘点效率
- 实时监测：可用于货架缺货预警与商品陈列巡查
- 业务落地：从算法、接口、数据库到前端页面形成完整系统
- 可扩展性强：支持模型替换、参数调优和后续功能扩展
- 展示效果好：适合课程设计、毕业设计和项目答辩展示

## 功能模块

### 1. 图片检测

- 上传单张货架图片进行检测
- 返回带标注框的结果图
- 统计空货架数量、商品数量和空置比例

### 2. 视频检测

- 上传本地视频进行离线检测
- 输出处理后的视频结果
- 支持将结果记录到历史中，便于回溯

### 3. 摄像头实时检测

- 接入摄像头进行实时巡检
- 动态分析货架状态变化
- 支持空货架数量的实时统计

### 4. 检测历史管理

- 保存检测记录到数据库
- 查看单次检测详情
- 删除历史记录及关联结果文件

### 5. 模型管理

- 获取当前可用模型列表
- 上传新的 YOLOv8 权重文件
- 在前端界面中切换不同模型

### 6. 算法配置

- 在线调整置信度阈值和 IOU 阈值
- 配置空货架检测相关参数
- 支持参数持久化保存与恢复默认值

### 7. 用户与权限管理

- 用户注册与登录
- 忘记密码与安全问题找回
- 管理员权限识别与功能控制

## 技术架构

### 前端

- Vue 3
- TypeScript
- Vite
- Element Plus
- Axios

### 后端

- FastAPI
- SQLAlchemy
- Pydantic
- PyMySQL
- Uvicorn

### AI 与图像处理

- Ultralytics YOLOv8
- PyTorch
- OpenCV
- NumPy
- Pillow

### 数据存储

- MySQL
- 本地文件系统

## 系统结构

```text
project/
├─ backend/                         # 后端服务
│  └─ app/
│     ├─ routes/                    # 认证、检测、配置、管理接口
│     ├─ services/                  # YOLO 检测服务与业务逻辑
│     ├─ config.py                  # 系统配置
│     ├─ config_manager.py          # 配置持久化管理
│     ├─ db.py                      # 数据库连接
│     ├─ models.py                  # SQLAlchemy 模型
│     ├─ schemas.py                 # Pydantic 数据结构
│     └─ main.py                    # FastAPI 应用入口
├─ frontend/                        # 前端应用
│  ├─ src/
│  │  ├─ App.vue                    # 主页面
│  │  └─ components/                # 功能组件
│  └─ package.json
├─ algorithm_config.json            # 算法配置文件
├─ init_directories.py              # 初始化输出目录
├─ manage_database.py               # 数据库管理脚本
├─ update_database.py               # 数据库结构更新脚本
├─ start.py                         # 一键启动脚本
├─ requirements.txt                 # Python 依赖
└─ yolov8n.pt                       # 示例模型文件
```

## 运行环境

- Python 3.9+
- Node.js 18+
- MySQL 8.0+
- Windows 环境下建议使用现有 Conda 环境 `yolo`

## 安装与启动

### 1. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 配置数据库

当前项目默认数据库连接位于 `backend/app/config.py`：

```text
mysql+pymysql://root:202217@localhost:3306/ultralytics_auth
```

运行前请按本机环境调整：

- 数据库用户名
- 数据库密码
- 数据库名称

也可以通过环境变量覆盖：

- `DATABASE_URL`
- `YOLO_WEIGHTS`
- `MODEL_DIR`
- `OUTPUT_DIR`

### 4. 初始化目录

```bash
python init_directories.py
```

### 5. 启动项目

分别启动前后端：

```bash
uvicorn backend.app.main:app --reload --port 8000
```

```bash
cd frontend
npm run dev
```

或使用一键启动脚本：

```bash
python start.py
```

默认访问地址：

- 前端：[http://localhost:5173](http://localhost:5173)
- 后端：[http://localhost:8000](http://localhost:8000)
- API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)

## 主要接口

- `POST /api/detect`
  图片、视频、摄像头检测入口
- `GET /api/models`
  获取可用模型列表
- `POST /api/upload_model`
  上传模型文件
- `GET /api/detections/`
  获取检测历史记录
- `GET /api/detections/{record_id}`
  获取检测详情
- `DELETE /api/detections/{record_id}`
  删除检测记录
- `GET /api/config/detection`
  获取算法配置
- `PUT /api/config/detection`
  更新算法配置
- `GET /api/config/thresholds`
  获取阈值配置
- `PUT /api/config/thresholds`
  更新阈值配置

## 答辩展示亮点

- 完成了从 YOLO 检测模型到业务系统应用的整体实现
- 支持图片、视频、摄像头三种检测输入方式
- 引入空货架推断逻辑，提升了实际零售场景适配性
- 前后端分离，具备较完整的交互、接口与数据存储能力
- 支持模型管理、历史记录和参数调优，系统扩展性较强

## 适用场景

- 超市货架缺货监测
- 便利店商品陈列巡检
- 仓储货位状态识别
- 零售场景智能视频分析

## 当前说明

- 当前仓库中部分路径仍为本机绝对路径，换机器运行前需要调整配置
- 当前正式后端入口为 `backend/app/main.py`
- 根目录下旧版 `main.py` 更偏早期实验文件，正式运行建议使用当前分层结构

## 后续优化方向

- 增加 Docker 部署方案
- 增加日志系统与异常监控
- 改进密码加密与权限设计
- 增加统计图表和数据看板
- 支持更规范的跨机器部署配置
