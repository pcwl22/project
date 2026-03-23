# components 目录说明

## 用途
存放 Vue 3 组件文件

## 组件列表

### 1. Login.vue
**用户登录/注册组件**

功能：
- 用户登录表单
- 用户注册表单
- 表单验证
- 登录状态管理

Props：无

Events：
- `login-success(userId, isAdmin)` - 登录成功事件

使用示例：
```vue
<Login @login-success="handleLoginSuccess" />
```

---

### 2. ImageDetection.vue
**图片检测组件**

功能：
- 图片上传（拖拽/点击）
- 实时检测
- 参数调整（置信度、IOU、模型选择）
- 结果可视化（Canvas 绘制检测框）
- 统计信息展示
- 图片下载

Props：
- `currentUserId` (可选) - 当前用户ID

主要方法：
- `handleUpload()` - 处理图片上传
- `handleDetect()` - 执行检测
- `drawDetections()` - 绘制检测框

---

### 3. VideoDetection.vue
**视频检测组件**

功能：
- 视频文件上传
- 实时视频检测
- 帧率控制
- 检测结果展示

Props：
- `currentUserId` (可选) - 当前用户ID

注意：
- 视频检测较消耗资源
- 建议使用较短的视频进行测试

---

### 4. ModelManagement.vue
**模型管理组件**

功能：
- 模型文件上传（.pt 格式）
- 模型列表展示
- 模型切换
- 上传进度显示

Props：无

API 调用：
- `POST /upload_model` - 上传模型

文件限制：
- 格式：.pt (PyTorch 模型)
- 大小：建议不超过 500MB

---

### 5. HistoryView.vue
**检测历史记录组件**

功能：
- 历史记录列表（分页）
- 记录详情查看
- 图片预览（原图/标注图）
- 记录删除（单个/批量）
- 图片下载
- 统计信息展示

Props：
- `currentUserId` (可选) - 当前用户ID
- `isAdmin` (可选) - 是否管理员

API 调用：
- `GET /detections/` - 获取历史列表
- `GET /detections/{id}` - 获取记录详情
- `DELETE /detections/{id}` - 删除记录
- `GET /detections/{id}/original` - 获取原图
- `GET /detections/{id}/annotated` - 获取标注图

---

## 组件开发规范

### 1. 文件命名
- 使用 PascalCase（大驼峰）
- 组件名应具有描述性
- 例：`ImageDetection.vue`

### 2. 组件结构
```vue
<template>
  <!-- 模板 -->
</template>

<script setup lang="ts">
// 导入
import { ref, reactive } from 'vue'

// 类型定义
interface Props {
  // ...
}

// Props 和 Emits
const props = defineProps<Props>()
const emit = defineEmits<{
  eventName: [param: string]
}>()

// 响应式数据
const data = ref('')

// 方法
const handleAction = () => {
  // ...
}
</script>

<style scoped>
/* 样式 */
</style>
```

### 3. 最佳实践
- 使用 Composition API
- 添加 TypeScript 类型
- 使用 `<script setup>` 语法
- 样式使用 `scoped` 避免污染
- 合理拆分大组件
- 添加适当的注释

### 4. 状态管理
- 简单状态：使用 `ref` / `reactive`
- 跨组件状态：使用 Props / Emits
- 全局状态：使用 LocalStorage 或 Pinia

### 5. API 调用
- 统一使用 Axios
- 添加错误处理
- 使用 Loading 状态
- 显示友好的错误提示

### 6. 性能优化
- 使用 `v-show` vs `v-if`
- 列表使用 `key`
- 避免不必要的计算
- 图片懒加载

## 添加新组件

1. 在此目录创建 `.vue` 文件
2. 定义组件结构（template, script, style）
3. 在父组件中导入使用：
   ```vue
   <script setup>
   import NewComponent from './components/NewComponent.vue'
   </script>
   
   <template>
     <NewComponent />
   </template>
   ```

## 调试技巧

1. **Vue DevTools**: 安装浏览器扩展
2. **Console.log**: 调试数据流
3. **Network**: 检查 API 请求
4. **Breakpoints**: 使用浏览器断点调试

## 常见问题

### 1. 组件不渲染
- 检查是否正确导入
- 检查组件名是否正确
- 查看控制台错误信息

### 2. 数据不更新
- 确保使用 `ref` 或 `reactive`
- 检查数据绑定语法
- 使用 Vue DevTools 查看数据

### 3. 样式不生效
- 检查 `scoped` 属性
- 查看样式优先级
- 使用浏览器开发工具检查

### 4. API 调用失败
- 检查网络请求
- 确认后端服务运行
- 查看代理配置
