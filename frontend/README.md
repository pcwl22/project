# 前端目录

基于 Vue 3 + TypeScript + Vite 的前端应用程序。

## 技术栈
- **Vue 3**: 渐进式 JavaScript 框架
- **TypeScript**: 类型安全的 JavaScript 超集
- **Vite**: 下一代前端构建工具
- **Element Plus**: Vue 3 UI 组件库
- **Axios**: HTTP 客户端

## 目录结构

```
frontend/
├── src/                    # 源代码目录
│   ├── components/         # Vue 组件
│   │   ├── Login.vue      # 登录组件
│   │   ├── ImageDetection.vue    # 图片检测
│   │   ├── VideoDetection.vue    # 视频检测
│   │   ├── ModelManagement.vue   # 模型管理
│   │   └── HistoryView.vue       # 历史记录
│   ├── App.vue            # 根组件
│   ├── main.ts            # 应用入口
│   └── style.css          # 全局样式
├── public/                # 静态资源目录
├── dist/                  # 构建输出目录
├── index.html             # HTML 入口文件
├── vite.config.ts         # Vite 配置文件
├── package.json           # 项目依赖配置
└── tsconfig.json          # TypeScript 配置

```

## 主要功能模块

### 1. 用户认证 (Login.vue)
- 用户登录
- 用户注册
- 会话管理

### 2. 图片检测 (ImageDetection.vue)
- 上传图片
- 实时检测
- 参数调整（置信度、IOU）
- 结果可视化
- 统计信息展示

### 3. 视频检测 (VideoDetection.vue)
- 视频上传
- 实时检测
- 帧率控制

### 4. 模型管理 (ModelManagement.vue)
- 模型上传
- 模型列表
- 模型切换

### 5. 历史记录 (HistoryView.vue)
- 检测历史列表
- 记录详情查看
- 图片下载
- 记录删除

## 开发指南

### 安装依赖
```bash
npm install
```

### 开发模式
```bash
npm run dev
```
访问：http://localhost:5176

### 构建生产版本
```bash
npm run build
```

### 预览生产构建
```bash
npm run preview
```

## 配置说明

### vite.config.ts
- **端口配置**: 5176
- **代理配置**: `/api` 代理到后端 `http://localhost:8000`
- **跨域处理**: 通过代理解决跨域问题

### API 基础路径
所有 API 请求使用 `/api` 前缀，通过 Vite 代理转发到后端。

示例：
```typescript
// 前端请求
axios.post('/api/auth/login', data)

// 实际请求
http://localhost:8000/api/auth/login
```

## 组件通信

### Props
父组件向子组件传递数据

### Events
子组件向父组件发送事件

### LocalStorage
存储用户登录信息：
- `userId`: 用户ID
- `username`: 用户名
- `isAdmin`: 是否管理员

## 样式规范
- 使用 Element Plus 主题色
- 响应式布局
- 统一的间距和字体大小
- 深色主题支持

## 注意事项
1. 所有 API 调用应添加错误处理
2. 使用 TypeScript 类型定义
3. 组件应保持单一职责
4. 避免直接操作 DOM
5. 使用 Vue 3 Composition API

## 常见问题

### 1. 代理不生效
- 确保后端服务运行在 8000 端口
- 重启前端开发服务器
- 清除浏览器缓存

### 2. 组件不更新
- 检查响应式数据定义
- 使用 `ref` 或 `reactive` 包装数据

### 3. 类型错误
- 检查 TypeScript 类型定义
- 运行 `npm run type-check`
