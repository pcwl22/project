<template>
  <el-config-provider :locale="zhCn">
    <div v-if="!isLoggedIn">
      <Login @login-success="handleLoginSuccess" />
    </div>
    <div v-else class="main-app">
      <!-- 顶部导航栏 -->
      <div class="app-header">
        <div class="header-content">
          <div class="logo-section">
            <h1>超市空货架检测系统</h1>
            <span class="subtitle">基于 YOLOv8 的智能货架监测与分析</span>
          </div>
          <div class="user-section">
            <el-button type="danger" @click="handleLogout" plain>退出登录</el-button>
          </div>
        </div>
      </div>

      <!-- 主内容区域 -->
      <div class="container">
        <el-tabs v-model="activeTab" class="main-tabs">
          <el-tab-pane label="图片检测" name="image">
            <ImageDetection 
              :model-list="modelList" 
              :current-user-id="currentUserId"
              @detection-complete="handleDetectionComplete"
            />
          </el-tab-pane>

          <el-tab-pane label="视频检测" name="video">
            <VideoDetection 
              :model-list="modelList"
              @detection-complete="handleVideoDetectionComplete"
            />
          </el-tab-pane>

          <el-tab-pane label="检测历史" name="history">
            <HistoryView ref="historyViewRef" />
          </el-tab-pane>

          <el-tab-pane label="用户管理" name="users" v-if="isAdmin">
            <UserManagement :is-admin="isAdmin" />
          </el-tab-pane>

          <el-tab-pane label="模型管理" name="model">
            <ModelManagement 
              v-model:current-model="currentModel"
              v-model:model-list="modelList"
            />
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </el-config-provider>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import HistoryView from './components/HistoryView.vue'
import Login from './components/Login.vue'
import ImageDetection from './components/ImageDetection.vue'
import VideoDetection from './components/VideoDetection.vue'
import ModelManagement from './components/ModelManagement.vue'
import UserManagement from './components/UserManagement.vue'

const isLoggedIn = ref(false)
const currentUserId = ref<number | null>(null)
const isAdmin = ref(false)

const handleLoginSuccess = (userId: number, isAdminUser: boolean = false) => {
  isLoggedIn.value = true
  currentUserId.value = userId
  isAdmin.value = isAdminUser
  localStorage.setItem('userId', userId.toString())
  localStorage.setItem('isAdmin', isAdminUser.toString())
}

const handleLogout = () => {
  isLoggedIn.value = false
  currentUserId.value = null
  isAdmin.value = false
  localStorage.removeItem('userId')
  localStorage.removeItem('isAdmin')
  ElMessage.success('已退出登录')
}

const activeTab = ref('image')

// 模型相关
const currentModel = ref('')
const modelList = ref(['best.pt', 'yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', 'yolov8l.pt', 'yolov8x.pt'])

const historyViewRef = ref()

const handleDetectionComplete = async (record: any) => {
  if (historyViewRef.value) {
    await historyViewRef.value.handleDetectionComplete(record)
  }
}

const handleVideoDetectionComplete = async () => {
  if (historyViewRef.value) {
    await historyViewRef.value.fetchHistory()
  }
}
</script>

<style scoped>
.main-app {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

/* 顶部导航栏 */
.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
  animation: slideDown 0.5s ease-out;
}

@keyframes slideDown {
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-section h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: white;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  margin-left: 15px;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 15px;
}

/* 主内容区域 */
.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 30px 40px;
}

.main-tabs {
  background: white;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  animation: fadeInScale 0.6s ease-out;
}

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.98);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

:deep(.el-tabs__header) {
  margin-bottom: 30px;
}

:deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 500;
  padding: 0 25px;
  height: 50px;
  line-height: 50px;
}

:deep(.el-tabs__item.is-active) {
  color: #667eea;
}

:deep(.el-tabs__active-bar) {
  height: 3px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

:deep(.el-button) {
  border-radius: 8px;
  padding: 12px 30px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  position: relative;
  overflow: hidden;
}

:deep(.el-button--primary::after) {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.5);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

:deep(.el-button--primary:active::after) {
  width: 200px;
  height: 200px;
}

:deep(.el-button--primary:hover) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

:deep(.el-button--success) {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  border: none;
  position: relative;
  overflow: hidden;
}

:deep(.el-button--success::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  transition: left 0.5s;
}

:deep(.el-button--success:hover::before) {
  left: 100%;
}

:deep(.el-button--success:hover) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(67, 233, 123, 0.4);
}
</style>
