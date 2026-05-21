# ShelfDetect

基于 YOLOv8 的智能货架检测与空货架识别系统。本项目面向零售货架巡检场景，支持图片检测、视频检测、摄像头实时检测、历史记录管理、模型管理、用户管理和算法参数配置，可用于商品陈列监测、缺货预警和课程/毕业设计展示。

## 项目简介

传统人工巡检方式在超市、便利店和仓储货架管理中存在效率低、主观性强、响应慢等问题。为提升货架巡检的自动化水平，本项目以 YOLOv8 目标检测模型为核心，构建了一套前后端分离的货架检测系统，实现对货架商品和空货架区域的识别、统计与结果可视化。

项目重点不仅在于完成目标检测，还进一步结合货架场景做了业务化封装，包括：

- 面向图片、视频、摄像头的多输入检测
- 空货架数量与占比统计
- 检测历史保存与回溯
- 模型切换与上传管理
- 算法阈值在线配置
- 用户登录、管理员权限控制

## 功能模块

### 1. 图片检测

- 上传单张货架图片
- 返回标注结果图
- 统计空货架数量、总货位数量、空置比例

### 2. 视频检测

- 上传本地视频进行离线检测
- 输出带检测框的视频结果
- 记录检测历史，便于后续查看

### 3. 摄像头实时检测

- 接入摄像头画面进行实时分析
- 支持持续检测货架状态
- 统计实时空货架情况

### 4. 历史记录管理

- 保存检测记录到数据库
- 支持查看检测详情
- 支持删除历史记录及关联文件

### 5. 模型管理

- 获取当前可用 `.pt` 模型列表
- 上传新的 YOLOv8 权重文件
- 前端可切换不同检测模型

### 6. 算法参数配置

- 在线调整置信度阈值和 IOU 阈值
- 配置空货架检测相关参数
- 支持持久化保存与恢复默认值

### 7. 用户与权限管理

- 用户注册与登录
- 找回密码
- 管理员权限识别与管理功能控制

## 技术方案

### 前端

- Vue 3
- TypeScript
- Vite
- Element Plus

### 后端

- FastAPI
- SQLAlchemy
- PyMySQL
- Pydantic

### 视觉与数据处理

- Ultralytics YOLOv8
- OpenCV
- NumPy

### 数据存储

- MySQL

## 系统结构

```text
project/
├─ backend/
│  └─ app/
│     ├─ routes/                 # 认证、检测、配置、管理接口
│     ├─ services/               # YOLO 检测服务
│     ├─ config.py               # 后端配置
│     ├─ config_manager.py       # 配置持久化管理
│     ├─ db.py                   # 数据库连接
│     ├─ models.py               # 数据模型
│     └─ main.py                 # FastAPI 入口
├─ frontend/
│  ├─ src/
│  │  ├─ App.vue                 # 主页面
│  │  └─ components/             # 图片、视频、摄像头、历史、模型、配置等组件
│  └─ package.json
├─ algorithm_config.json         # 算法配置文件
├─ init_directories.py           # 初始化输出目录
├─ manage_database.py            # 数据库管理脚本
├─ update_database.py            # 数据库结构更新脚本
├─ start.py                      # 一键启动脚本
└─ yolov8n.pt                    # 示例模型文件
```

## 运行环境

- Python 3.9 及以上
- Node.js 18 及以上
- MySQL 8.0 及以上
- Windows 环境下建议使用与项目一致的 Conda/Python 环境

## 安装步骤

### 1. 安装后端依赖

项目根目录已提供 `requirements.txt`：

```bash
pip install -r requirements.txt
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 配置数据库

默认数据库配置位于 `backend/app/config.py`，使用的是本地 MySQL：

```text
mysql+pymysql://root:202217@localhost:3306/ultralytics_auth
```

运行前请根据自己的环境修改：

- 数据库用户名
- 数据库密码
- 数据库名称

也可以通过环境变量覆盖：

- `DATABASE_URL`
- `YOLO_WEIGHTS`
- `MODEL_DIR`
- `OUTPUT_DIR`

### 4. 初始化输出目录

```bash
python init_directories.py
```

## 启动方式

### 方式一：分别启动前后端

启动后端：

```bash
uvicorn backend.app.main:app --reload --port 8000
```

启动前端：

```bash
cd frontend
npm run dev
```

### 方式二：一键启动

```bash
python start.py
```

默认访问地址：

- 前端：[http://localhost:5173](http://localhost:5173)
- 后端：[http://localhost:8000](http://localhost:8000)
- API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)

## 核心接口

- `POST /api/detect`
  用于图片、视频、摄像头检测
- `GET /api/models`
  获取可用模型列表
- `POST /api/upload_model`
  上传模型文件
- `GET /api/detections/`
  获取检测历史
- `GET /api/detections/{record_id}`
  获取检测详情
- `DELETE /api/detections/{record_id}`
  删除检测记录
- `GET /api/config/detection`
  获取算法配置
- `PUT /api/config/detection`
  更新算法配置
- `GET /api/config/thresholds`
  获取检测阈值
- `PUT /api/config/thresholds`
  更新检测阈值

## 毕业设计展示可强调的亮点

- 完成了从模型检测到业务系统落地的完整闭环，而不只是单独训练模型
- 支持图片、视频、摄像头三种输入形式，应用场景更完整
- 检测结果可持久化保存，具备历史追踪能力
- 提供模型管理与参数调节能力，系统具有一定可扩展性
- 前后端分离，界面交互与接口设计较完整，适合演示和答辩展示

## 适用场景

- 超市货架缺货监测
- 便利店商品陈列巡检
- 仓储货位状态识别
- 零售场景智能视频分析

## 当前说明

- 当前仓库中部分路径仍是本机绝对路径，换机器运行前需要调整配置
- 当前实际使用的后端入口是 `backend/app/main.py`
- 根目录下旧版 `main.py` 更像早期实验文件，正式运行建议使用当前分层后的后端结构

## 后续可优化方向

- 增加 Docker 部署方案
- 增加日志系统与异常监控
- 引入更安全的密码加密方式
- 增加角色权限细分
- 支持检测结果图表分析与数据看板
