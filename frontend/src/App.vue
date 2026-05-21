<template>
  <el-config-provider :locale="zhCn">
    <div v-if="!isLoggedIn">
      <Login @login-success="handleLoginSuccess" />
    </div>
    <div v-else class="app-layout">
      <!-- Sidebar -->
      <aside class="sidebar glass-card">
        <div class="logo-container">
          <div class="logo-icon">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="logo-text">
            <h1>ShelfDetect</h1>
          </div>
        </div>
        
        <nav class="nav-menu">
          <div 
            v-for="item in menuItems" 
            :key="item.id"
            class="nav-item"
            :class="{ active: activeTab === item.id }"
            @click="activeTab = item.id"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
            <div class="active-indicator" v-if="activeTab === item.id"></div>
          </div>
        </nav>

        <div class="user-profile">
          <div class="avatar">
            <el-icon><UserFilled /></el-icon>
          </div>
          <div class="user-info">
            <span class="username">User #{{ currentUserId }}</span>
            <span class="role">{{ isAdmin ? 'Administrator' : 'Operator' }}</span>
          </div>
          <el-button circle text @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
          </el-button>
        </div>
      </aside>

      <!-- Main Content -->
      <main class="main-content">
        <header class="top-header glass-card">
          <div class="breadcrumb">
            <span class="page-title">{{ getCurrentPageTitle() }}</span>
            <span class="page-desc">{{ getCurrentPageDesc() }}</span>
          </div>
        </header>

        <div class="content-wrapper">
          <transition name="fade-slide" mode="out-in">
            <div :key="activeTab" class="content-inner">
              <ImageDetection 
                v-if="activeTab === 'image'"
                :model-list="modelList" 
                :current-user-id="currentUserId"
                v-model:selected-model="currentModel"
                @detection-complete="handleDetectionComplete"
              />

              <VideoDetection 
                v-if="activeTab === 'video'"
                :model-list="modelList"
                v-model:selected-model="currentModel"
                @detection-complete="handleVideoDetectionComplete"
              />

              <CameraDetection 
                v-if="activeTab === 'camera'"
                v-model:selected-model="currentModel"
                :model-list="modelList"
              />

              <HistoryView 
                v-if="activeTab === 'history'"
                ref="historyViewRef" 
              />

              <UserManagement 
                v-if="activeTab === 'users' && isAdmin"
                :is-admin="isAdmin" 
              />

              <ModelManagement 
                v-if="activeTab === 'model'"
                v-model:current-model="currentModel"
                v-model:model-list="modelList"
                :is-admin="isAdmin"
              />

              <AlgorithmSettings 
                v-if="activeTab === 'settings'"
              />
            </div>
          </transition>
        </div>
      </main>
    </div>
  </el-config-provider>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import HistoryView from './components/HistoryView.vue'
import Login from './components/Login.vue'
import ImageDetection from './components/ImageDetection.vue'
import VideoDetection from './components/VideoDetection.vue'
import CameraDetection from './components/CameraDetection.vue'
import ModelManagement from './components/ModelManagement.vue'
import UserManagement from './components/UserManagement.vue'
import AlgorithmSettings from './components/AlgorithmSettings.vue'

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

const menuItems = computed(() => {
  const items = [
    { id: 'image', label: '图片检测', icon: 'Picture' },
    { id: 'video', label: '视频检测', icon: 'VideoCamera' },
    { id: 'camera', label: '摄像头检测', icon: 'Camera' },
    { id: 'history', label: '检测历史', icon: 'Clock' },
    { id: 'settings', label: '算法设置', icon: 'Setting' },
    { id: 'model', label: '模型管理', icon: 'Cpu' },
  ]
  
  if (isAdmin.value) {
    items.push({ id: 'users', label: '用户管理', icon: 'User' })
  }
  
  return items
})

const getCurrentPageTitle = () => {
  const item = menuItems.value.find(i => i.id === activeTab.value)
  return item ? item.label : ''
}

const getCurrentPageDesc = () => {
  const map: Record<string, string> = {
    image: '上传图片进行智能货架空缺检测',
    video: '处理监控视频流并分析货架状态',
    camera: '使用摄像头进行实时货架检测',
    history: '查看过往的检测记录和统计数据',
    settings: '调整空货架检测算法参数',
    model: '管理和更新 YOLOv8 检测模型',
    users: '系统用户权限与账户管理'
  }
  return map[activeTab.value] || ''
}

// 模型相关
const currentModel = ref('best.pt')  // 默认模型
const modelList = ref<string[]>([])

// 从后端获取模型列表
const fetchModelList = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/models')
    const data = await response.json()
    
    if (data.models && data.models.length > 0) {
      modelList.value = data.models
      localStorage.setItem('modelList', JSON.stringify(data.models))
      console.log('✅ 已从服务器更新模型列表:', data.models)
      
      // 如果当前选择的模型不在列表中，切换到第一个模型
      if (!data.models.includes(currentModel.value)) {
        console.log(`⚠️ 当前模型 ${currentModel.value} 不存在，切换到 ${data.models[0]}`)
        currentModel.value = data.models[0]
      }
    }
  } catch (error) {
    console.error('❌ 获取模型列表失败:', error)
    // 失败时从 localStorage 加载
    loadModelListFromStorage()
  }
}

// 从 localStorage 加载模型列表（备用方案）
const loadModelListFromStorage = () => {
  const savedList = localStorage.getItem('modelList')
  if (savedList) {
    try {
      modelList.value = JSON.parse(savedList)
      console.log('📦 从缓存加载模型列表:', modelList.value)
    } catch (e) {
      console.error('Failed to parse model list:', e)
      modelList.value = ['best.pt', 'yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', 'yolov8l.pt', 'yolov8x.pt']
    }
  } else {
    modelList.value = ['best.pt', 'yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', 'yolov8l.pt', 'yolov8x.pt']
  }
}

// 从 localStorage 加载当前选择的模型
const loadCurrentModel = () => {
  const savedModel = localStorage.getItem('currentModel')
  if (savedModel) {
    currentModel.value = savedModel
    console.log('已加载上次使用的模型:', savedModel)
  }
}

// 保存模型列表到 localStorage
const saveModelList = (list: string[]) => {
  modelList.value = list
  localStorage.setItem('modelList', JSON.stringify(list))
}

// 初始化：先加载缓存，再从服务器更新
loadCurrentModel()
loadModelListFromStorage()
fetchModelList()

// 定期从服务器刷新模型列表（每30秒）
let modelRefreshTimer: number | null = null
const startModelRefresh = () => {
  // 清除旧的定时器
  if (modelRefreshTimer) {
    clearInterval(modelRefreshTimer)
  }
  
  // 每30秒刷新一次
  modelRefreshTimer = setInterval(() => {
    console.log('🔄 定期刷新模型列表...')
    fetchModelList()
  }, 30000) // 30秒
}

// 停止定期刷新
const stopModelRefresh = () => {
  if (modelRefreshTimer) {
    clearInterval(modelRefreshTimer)
    modelRefreshTimer = null
  }
}

// 组件挂载时启动定期刷新
onMounted(() => {
  startModelRefresh()
  console.log('✅ 已启动模型列表自动刷新（每30秒）')
})

// 组件卸载时停止定期刷新
onUnmounted(() => {
  stopModelRefresh()
  console.log('🛑 已停止模型列表自动刷新')
})

// 监听 currentModel 的变化，自动保存到 localStorage
watch(currentModel, (newModel) => {
  localStorage.setItem('currentModel', newModel)
  console.log('当前模型已更新:', newModel)
})

// 监听 modelList 的变化，自动保存到 localStorage
watch(modelList, (newList) => {
  localStorage.setItem('modelList', JSON.stringify(newList))
  console.log('模型列表已更新:', newList)
}, { deep: true })

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
.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: var(--bg-gradient);
}

/* Sidebar Styles */
.sidebar {
  width: 280px;
  height: calc(100vh - 40px);
  margin: 20px;
  display: flex;
  flex-direction: column;
  padding: 24px;
  background: rgba(255, 255, 255, 0.9);
  z-index: 100;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 40px;
  padding: 0 12px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.logo-text h1 {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
}

.logo-text span {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.nav-menu {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.nav-item:hover {
  background: rgba(99, 102, 241, 0.05);
  color: var(--primary-color);
}

.nav-item.active {
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.1), transparent);
  color: var(--primary-color);
  font-weight: 600;
}

.nav-item .el-icon {
  font-size: 20px;
}

.active-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--primary-color);
  border-radius: 0 4px 4px 0;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(243, 244, 246, 0.6);
  border-radius: 12px;
  margin-top: auto;
}

.avatar {
  width: 36px;
  height: 36px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.username {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.role {
  font-size: 12px;
  color: var(--text-secondary);
}

/* Main Content Styles */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px 20px 20px 0;
  overflow: hidden;
}

.top-header {
  height: 70px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  background: rgba(255, 255, 255, 0.8);
}

.breadcrumb {
  display: flex;
  flex-direction: column;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.page-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.content-wrapper {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px; /* For scrollbar space */
}

.content-inner {
  min-height: 100%;
}

/* Animations */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
</style>
