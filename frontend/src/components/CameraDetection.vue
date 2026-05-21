<template>
  <div class="camera-detection">
    <el-card class="control-card glass-card">
      <template #header>
        <div class="card-header">
          <el-icon><VideoCamera /></el-icon>
          <span>摄像头实时检测</span>
        </div>
      </template>

      <div class="controls">
        <div class="control-item">
          <label>检测模型</label>
          <el-select v-model="selectedModel" placeholder="选择模型">
            <el-option
              v-for="model in modelList"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </div>

        <div class="control-item">
          <label>摄像头设备</label>
          <el-select v-model="selectedCamera" placeholder="选择摄像头">
            <el-option
              v-for="camera in cameras"
              :key="camera.deviceId"
              :label="camera.label"
              :value="camera.deviceId"
            />
          </el-select>
        </div>

        <div class="control-item">
          <label>置信度阈值</label>
          <el-slider v-model="confidence" :min="0.1" :max="1" :step="0.05" show-input />
        </div>

        <div class="control-item">
          <label>IOU 阈值</label>
          <el-slider v-model="iouThreshold" :min="0.1" :max="1" :step="0.05" show-input />
        </div>

        <div class="control-item">
          <label>检测间隔 (秒)</label>
          <el-slider v-model="detectionInterval" :min="0.5" :max="5" :step="0.5" show-input />
        </div>

        <div class="button-group">
          <el-button 
            type="primary" 
            @click="toggleDetection"
            :loading="isStarting"
          >
            {{ isDetecting ? '停止检测' : '开始检测' }}
          </el-button>
          
          <el-button 
            @click="captureSnapshot"
            :disabled="!isDetecting"
          >
            拍摄快照
          </el-button>
        </div>
      </div>
    </el-card>

    <div class="video-container glass-card">
      <div class="video-wrapper">
        <video
          ref="videoElement"
          autoplay
          playsinline
          muted
          class="video-stream"
        ></video>

        <canvas
          ref="canvasElement"
          class="detection-canvas"
        ></canvas>

        <div class="status-indicator" :class="{ active: isDetecting }">
          <el-icon><VideoCamera /></el-icon>
          <span>{{ isDetecting ? '检测中...' : '未检测' }}</span>
        </div>
      </div>

      <div class="stats-panel" v-if="currentStats">
        <div class="stat-item">
          <span class="stat-label">商品数</span>
          <span class="stat-value">{{ currentStats.product_count }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">空货架</span>
          <span class="stat-value danger">{{ currentStats.empty_count }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">最大值</span>
          <span class="stat-value warning">{{ maxEmptyCount }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">缺货率</span>
          <span class="stat-value" :class="{ danger: currentStats.empty_rate > 0.2 }">
            {{ (currentStats.empty_rate * 100).toFixed(1) }}%
          </span>
        </div>
        <div class="stat-item">
          <span class="stat-label">FPS</span>
          <span class="stat-value">{{ fps.toFixed(1) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const props = defineProps<{
  selectedModel?: string
  modelList?: string[]
}>()

const emit = defineEmits<{
  (e: 'update:selectedModel', model: string): void
}>()

// 使用本地 ref 并通过 watch 同步
const selectedModel = ref(props.selectedModel || 'best.pt')

// 监听 props 变化，更新本地值
watch(() => props.selectedModel, (newVal) => {
  if (newVal && newVal !== selectedModel.value) {
    selectedModel.value = newVal
  }
})

// 监听本地值变化，emit 给父组件
watch(selectedModel, (newVal) => {
  emit('update:selectedModel', newVal)
})

// 默认模型列表
const modelList = ref(props.modelList || ['best.pt', 'yolov8n.pt', 'yolov8s.pt'])

// 监听 props.modelList 变化
watch(() => props.modelList, (newVal) => {
  if (newVal) {
    modelList.value = newVal
  }
})

interface Camera {
  deviceId: string
  label: string
}

interface DetectionStats {
  product_count: number
  empty_count: number
  total_slots: number
  empty_rate: number
}

interface Detection {
  x1: number
  y1: number
  x2: number
  y2: number
  confidence: number
  class_name: string
}

const videoElement = ref<HTMLVideoElement>()
const canvasElement = ref<HTMLCanvasElement>()
const cameras = ref<Camera[]>([])
const selectedCamera = ref('')
const confidence = ref(0.25)
const iouThreshold = ref(0.45)
const detectionInterval = ref(1.0)
const isDetecting = ref(false)
const isStarting = ref(false)
const currentStats = ref<DetectionStats | null>(null)
const fps = ref(0)
const maxEmptyCount = ref(0)  // 记录空货架最大值
const maxEmptyDetections = ref<Detection[]>([])  // 记录空货架最多的那一帧的检测框
const maxEmptyFrameBlob = ref<Blob | null>(null)  // 记录空货架最多的那一帧的图片
const sessionStartTime = ref<Date | null>(null)  // 记录会话开始时间

let mediaStream: MediaStream | null = null
let detectionTimer: number | null = null
let lastFrameTime = 0

const getCameras = async () => {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices()
    cameras.value = devices
      .filter(device => device.kind === 'videoinput')
      .map((device, index) => ({
        deviceId: device.deviceId,
        label: device.label || `摄像头 ${index + 1}`
      }))
    
    if (cameras.value.length > 0) {
      selectedCamera.value = cameras.value[0].deviceId
    }
  } catch (error) {
    console.error('获取摄像头列表失败:', error)
    ElMessage.error('无法访问摄像头设备')
  }
}

const startCamera = async () => {
  try {
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop())
    }

    const constraints = {
      video: {
        deviceId: selectedCamera.value ? { exact: selectedCamera.value } : undefined,
        width: { ideal: 1280 },
        height: { ideal: 720 }
      }
    }

    mediaStream = await navigator.mediaDevices.getUserMedia(constraints)
    
    if (videoElement.value) {
      videoElement.value.srcObject = mediaStream
      
      await new Promise<void>((resolve) => {
        if (videoElement.value) {
          videoElement.value.onloadedmetadata = () => resolve()
        }
      })

      if (canvasElement.value && videoElement.value) {
        canvasElement.value.width = videoElement.value.videoWidth
        canvasElement.value.height = videoElement.value.videoHeight
      }
    }
  } catch (error) {
    console.error('启动摄像头失败:', error)
    ElMessage.error('无法启动摄像头')
    throw error
  }
}

const stopCamera = () => {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  
  if (videoElement.value) {
    videoElement.value.srcObject = null
  }
}

const detectFrame = async () => {
  if (!videoElement.value || !canvasElement.value) return

  const canvas = canvasElement.value
  const video = videoElement.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  try {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

    const blob = await new Promise<Blob>((resolve) => {
      canvas.toBlob((b) => {
        if (b) resolve(b)
      }, 'image/jpeg', 0.8)
    })

    const formData = new FormData()
    formData.append('file', blob, 'frame.jpg')

    // 注意：这里不传 user_id 和 mode，避免保存到数据库
    // 只在停止检测时才保存记录
    const startTime = performance.now()
    const response = await axios.post(
      `http://localhost:8000/api/detect?model=${selectedModel.value}&conf=${confidence.value}&iou=${iouThreshold.value}`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    )

    const endTime = performance.now()
    const frameTime = endTime - lastFrameTime
    lastFrameTime = endTime
    fps.value = frameTime > 0 ? 1000 / frameTime : 0

    console.log('检测响应:', response.data)

    if (response.data && response.data.detections) {
      drawDetections(response.data.detections)
      
      const emptyCount = response.data.detections.filter((d: Detection) => 
        d.class_name.toLowerCase().includes('empty')
      ).length
      
      // 更新空货架最大值，并保存该帧的检测框
      if (emptyCount > maxEmptyCount.value) {
        maxEmptyCount.value = emptyCount
        maxEmptyDetections.value = response.data.detections  // 保存检测框数据
        
        // 保存该帧的截图（用于最后保存记录）
        canvas.toBlob((b) => {
          if (b) {
            maxEmptyFrameBlob.value = b
          }
        }, 'image/jpeg', 0.9)
      }
      
      currentStats.value = {
        product_count: response.data.detections.filter((d: Detection) => 
          !d.class_name.toLowerCase().includes('empty')
        ).length,
        empty_count: emptyCount,
        total_slots: response.data.detections.length,
        empty_rate: response.data.empty_rate || 0
      }
    }
  } catch (error) {
    console.error('检测失败:', error)
    if (axios.isAxiosError(error)) {
      console.error('错误详情:', error.response?.data)
    }
  }
}

const drawDetections = (detections: Detection[]) => {
  if (!canvasElement.value || !videoElement.value) return

  const canvas = canvasElement.value
  const video = videoElement.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

  detections.forEach((detection) => {
    const isEmptyShelf = detection.class_name.toLowerCase().includes('empty')
    
    ctx.strokeStyle = isEmptyShelf ? '#ff4444' : '#00ff00'
    ctx.fillStyle = isEmptyShelf ? 'rgba(255, 68, 68, 0.2)' : 'rgba(0, 255, 0, 0.2)'
    ctx.lineWidth = isEmptyShelf ? 3 : 2

    const width = detection.x2 - detection.x1
    const height = detection.y2 - detection.y1
    ctx.fillRect(detection.x1, detection.y1, width, height)
    ctx.strokeRect(detection.x1, detection.y1, width, height)

    const label = `${(detection.confidence * 100).toFixed(0)}%`
    ctx.font = '14px Arial'
    const textWidth = ctx.measureText(label).width
    
    ctx.fillStyle = isEmptyShelf ? '#ff4444' : '#00ff00'
    ctx.fillRect(detection.x1, detection.y1 - 25, textWidth + 10, 25)
    
    ctx.fillStyle = '#ffffff'
    ctx.fillText(label, detection.x1 + 5, detection.y1 - 7)
  })
}

const startDetection = async () => {
  if (!mediaStream) {
    await startCamera()
  }

  isDetecting.value = true
  lastFrameTime = performance.now()
  sessionStartTime.value = new Date()  // 记录会话开始时间
  maxEmptyCount.value = 0  // 重置空货架最大值
  maxEmptyDetections.value = []  // 重置检测框数据
  maxEmptyFrameBlob.value = null  // 重置图片数据

  const intervalMs = detectionInterval.value * 1000
  detectionTimer = window.setInterval(detectFrame, intervalMs)
  
  detectFrame()
}

const stopDetection = async () => {
  // 停止检测
  isDetecting.value = false
  
  if (detectionTimer) {
    clearInterval(detectionTimer)
    detectionTimer = null
  }

  // 只保存空货架最多的那一帧记录到数据库
  if (sessionStartTime.value && maxEmptyCount.value > 0 && maxEmptyFrameBlob.value) {
    try {
      await saveCameraSession()
      ElMessage.success(`摄像头检测记录已保存（空货架最大值: ${maxEmptyCount.value}）`)
    } catch (error) {
      console.error('保存摄像头检测记录失败:', error)
      ElMessage.error('保存检测记录失败')
    }
  }

  if (canvasElement.value) {
    const ctx = canvasElement.value.getContext('2d')
    if (ctx) {
      ctx.clearRect(0, 0, canvasElement.value.width, canvasElement.value.height)
    }
  }

  currentStats.value = null
  sessionStartTime.value = null
}

// 保存摄像头检测会话记录（只保存一次）
const saveCameraSession = async () => {
  try {
    const userId = localStorage.getItem('userId') || '0'
    
    // 使用保存的空货架最多的那一帧图片
    if (!maxEmptyFrameBlob.value) {
      console.warn('没有保存的最大空货架帧图片')
      return
    }
    
    const formData = new FormData()
    formData.append('file', maxEmptyFrameBlob.value, `camera_session_${Date.now()}.jpg`)
    
    // 将检测框数据转换为JSON字符串
    const detectionsJson = JSON.stringify(maxEmptyDetections.value)
    
    const response = await axios.post(
      `http://localhost:8000/api/detect?mode=camera&model=${selectedModel.value}&conf=${confidence.value}&iou=${iouThreshold.value}&user_id=${userId}&max_empty_count=${maxEmptyCount.value}&detections_json=${encodeURIComponent(detectionsJson)}`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    )
    
    console.log('保存摄像头记录响应:', response.data)
  } catch (error) {
    console.error('保存摄像头检测记录失败:', error)
    throw error
  }
}

const toggleDetection = async () => {
  if (isDetecting.value) {
    stopDetection()
  } else {
    isStarting.value = true
    try {
      await startDetection()
      ElMessage.success('开始实时检测')
    } catch (error) {
      ElMessage.error('启动检测失败')
    } finally {
      isStarting.value = false
    }
  }
}

const captureSnapshot = () => {
  if (!canvasElement.value) return

  try {
    const link = document.createElement('a')
    link.download = `snapshot_${Date.now()}.jpg`
    link.href = canvasElement.value.toDataURL('image/jpeg')
    link.click()
    
    ElMessage.success('快照已保存')
  } catch (error) {
    console.error('保存快照失败:', error)
    ElMessage.error('保存快照失败')
  }
}

// 加载保存的阈值
const loadThresholds = async () => {
  try {
    const response = await axios.get('/api/config/thresholds')
    if (response.data) {
      confidence.value = response.data.conf_threshold
      iouThreshold.value = response.data.iou_threshold
    }
  } catch (error) {
    console.error('加载阈值失败:', error)
  }
}

// 保存阈值
const saveThresholds = async () => {
  try {
    await axios.put('/api/config/thresholds', {
      conf_threshold: confidence.value,
      iou_threshold: iouThreshold.value
    })
  } catch (error) {
    console.error('保存阈值失败:', error)
  }
}

// 监听阈值变化并保存
watch([confidence, iouThreshold], () => {
  saveThresholds()
})

onMounted(async () => {
  await loadThresholds()
  await getCameras()
  if (cameras.value.length > 0) {
    await startCamera()
  }
})

onUnmounted(() => {
  stopDetection()
  stopCamera()
})
</script>

<style scoped>
.camera-detection {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 20px;
  height: 100%;
}

.control-card {
  height: fit-content;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.controls {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-item label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.button-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 10px;
}

.video-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
}

.video-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
}

.video-stream,
.detection-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.detection-canvas {
  pointer-events: none;
}

.status-indicator {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 20px;
  color: #999;
  font-size: 14px;
}

.status-indicator.active {
  background: rgba(255, 68, 68, 0.9);
  color: white;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.stats-panel {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 15px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px;
  background: rgba(243, 244, 246, 0.6);
  border-radius: 12px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--primary-color);
}

.stat-value.danger {
  color: #ff4444;
}

.stat-value.warning {
  color: #ff9800;
}
</style>
