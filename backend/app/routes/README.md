# routes 目录说明

## 用途
存放后端 API 路由定义文件

## 文件说明

### auth.py
用户认证相关接口：
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/forgot-password` - 忘记密码（验证用户名）
- `POST /api/auth/reset-password` - 重置密码（验证安全答案）

### detections.py
检测功能相关接口：
- `POST /api/upload_model` - 上传模型文件
- `POST /api/detect` - 图片检测（自动保存历史）
- `GET /api/detections/` - 获取检测历史记录列表
- `GET /api/detections/{id}` - 获取单条记录详情
- `DELETE /api/detections/{id}` - 删除检测记录
- `GET /api/detections/{id}/original` - 获取原始图片
- `GET /api/detections/{id}/annotated` - 获取标注图片

### admin.py
管理员功能相关接口（需要管理员权限）：
- `GET /api/admin/users` - 获取所有用户列表
- `DELETE /api/admin/users/{user_id}` - 删除用户（不能删除管理员）
- `GET /api/admin/stats` - 获取系统统计信息

## 路由注册
所有路由在 `backend/app/main.py` 中注册：
```python
app.include_router(auth_router)
app.include_router(detections_router)
app.include_router(admin_router)
```

## 添加新路由
1. 在此目录创建新的路由文件（如 `new_feature.py`）
2. 定义路由：
   ```python
   from fastapi import APIRouter
   router = APIRouter(prefix="/api/feature", tags=["feature"])
   
   @router.get("/")
   def get_feature():
       return {"message": "Hello"}
   ```
3. 在 `main.py` 中注册路由

## 注意事项
- 所有 API 路由建议使用 `/api` 前缀
- 使用合适的 HTTP 方法（GET/POST/PUT/DELETE）
- 添加适当的请求验证和错误处理
- 使用依赖注入获取数据库会话
