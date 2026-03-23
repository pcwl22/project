<template>
  <div class="upload-container glass-card">
    <el-select 
      v-model="selectedModel" 
      placeholder="选择模型权重"
      size="large"
      class="custom-select"
    >
      <el-option
        v-for="model in modelList"
        :key="model"
        :label="model"
        :value="model"
      />
    </el-select>
    
    <el-upload
      class="upload"
      action="/api/detect"
      :auto-upload="false"
      :show-file-list="false"
      :on-change="handleImageChange"
      accept="image/*"
    >
      <template #trigger>
        <el-button type="primary" class="action-button">
          <el-icon><Picture /></el-icon>
          选择图片
        </el-button>
      </template>
    </el-upload>
    
    <el-button
      type="success" 
      @click="uploadImage"
      :disabled="!imageFile"
      :loading="imageLoading"
      class="action-button"
    >
      <el-icon><CaretRight /></el-icon>
      开始检测
    </el-button>
  </div>
  
  <!-- 置信度和 IOU 阈值设置 -->
  <div class="threshold-container">
    <div class="threshold-card glass-card">
      <div class="threshold-item">
        <div class="threshold-label">
          <span>
            置信度阈值
            <el-tooltip content="控制检测结果的最低置信度，值越高，过滤越严格，误检越少" placement="top">
              <el-icon class="help-icon"><QuestionFilled /></el-icon>
            </el-tooltip>
          </span>
          <el-tag size="small" effect="dark" round>{{ confidence }}</el-tag>
        </div>
        <el-slider 
          v-model="confidence" 
          :min="0" 
          :max="1" 
          :step="0.05"
          show-stops
          class="custom-slider"
        />
      </div>
      <div class="threshold-item">
        <div class="threshold-label">
          <span>
            IOU 阈值
            <el-tooltip content="非极大值抑制阈值，控制重叠框的过滤，值越小，过滤越严格" placement="top">
              <el-icon class="help-icon"><QuestionFilled /></el-icon>
            </el-tooltip>
          </span>
          <el-tag size="small" effect="dark" round>{{ iouThreshold }}</el-tag>
        </div>
        <el-slider 
          v-model="iouThreshold" 
          :min="0" 
          :max="1" 
          :step="0.05"
          show-stops
          class="custom-slider"
        />
      </div>
    </div>
  </div>

  <!-- 检测进度条 -->
  <div v-if="imageLoading" class="progress-container glass-card">
    <el-progress 
      :percentage="detectProgress" 
      :format="formatProgress"
      :stroke-width="12"
      striped
      striped-flow
      :duration="5"
    />
    <p class="progress-text">正在分析图像...</p>
  </div>

  <!-- 检测统计信息 -->
  <div v-if="detections.length" class="stats-container">
    <h3 class="section-title">检测统计</h3>
    <div class="stats-card glass-card">
      <div class="stats-header">
        <div class="total-count">
          <span class="label">总数量</span>
          <span class="value">{{ getTotalDetections() }}</span>
        </div>
        <el-button type="primary" plain round @click="exportStats">
          <el-icon><Download /></el-icon>
          导出统计
        </el-button>
      </div>
      <el-table :data="statsTableData" stripe class="custom-table">
        <el-table-column prop="name" label="品种" />
        <el-table-column prop="count" label="数量" />
        <el-table-column prop="percentage" label="占比">
          <template #default="scope">
            <el-progress :percentage="scope.row.percentage" :format="percentageFormat" />
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>

  <div class="preview-container" v-if="imageUrl">
    <div class="image-wrapper glass-card">
      <div class="image-header">
        <h3>原始图片</h3>
        <div class="toolbar">
          <el-button-group>
            <el-button size="small" @click="zoomIn('original')" icon="ZoomIn" circle></el-button>
            <el-button size="small" @click="zoomOut('original')" icon="ZoomOut" circle></el-button>
            <el-button size="small" @click="resetZoom('original')" icon="RefreshRight" circle></el-button>
          </el-button-group>
        </div>
      </div>
      <div 
        class="image-zoom-container" 
        @wheel.prevent="handleWheel($event, 'original')"
        @mousedown="startDrag($event, 'original')"
        @mousemove="onDrag($event, 'original')"
        @mouseup="endDrag('original')"
        @mouseleave="endDrag('original')"
      >
        <div 
          :style="{ 
            transform: `scale(${originalZoom}) translate(${originalPosition.x}px, ${originalPosition.y}px)`,
            transition: isDragging.original ? 'none' : 'transform 0.3s'
          }"
        >
          <el-image 
            :src="imageUrl" 
            fit="contain"
            :preview-src-list="[imageUrl]"
            :initial-index="0"
            preview-teleported
          />
        </div>
      </div>
    </div>
    <div class="image-wrapper glass-card" v-if="detections.length">
      <div class="image-header">
        <h3>检测结果</h3>
        <div class="toolbar">
          <el-button-group>
            <el-button size="small" @click="zoomIn('result')" icon="ZoomIn" circle></el-button>
            <el-button size="small" @click="zoomOut('result')" icon="ZoomOut" circle></el-button>
            <el-button size="small" @click="resetZoom('result')" icon="RefreshRight" circle></el-button>
          </el-button-group>
          <el-button size="small" type="primary" @click="downloadResult" icon="Download" round class="ml-2">下载</el-button>
        </div>
      </div>
      <div 
        class="image-zoom-container" 
        @wheel.prevent="handleWheel($event, 'result')"
        @mousedown="startDrag($event, 'result')"
        @mousemove="onDrag($event, 'result')"
        @mouseup="endDrag('result')"
        @mouseleave="endDrag('result')"
      >
        <div 
          class="canvas-container" 
          :style="{ 
            transform: `scale(${resultZoom}) translate(${resultPosition.x}px, ${resultPosition.y}px)`,
            transition: isDragging.result ? 'none' : 'transform 0.3s'
          }"
        >
          <img :src="imageUrl" ref="resultImage" @load="drawDetections" />
          <canvas ref="canvas" class="detection-canvas"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { QuestionFilled, ZoomIn, ZoomOut, RefreshRight, Download, Picture, CaretRight } from '@element-plus/icons-vue'

const props = defineProps<{
  modelList: string[]
  currentUserId: number | null
}>()

const emit = defineEmits<{
  (e: 'detection-complete', record: any): void
}>()

interface Detection {
  x1: number
  y1: number
  x2: number
  y2: number
  confidence: number
  class: number
  class_name: string
}

interface DetectionStats {
  [key: string]: number
}

interface StatsTableRow {
  name: string
  count: number
  percentage: number
}

const selectedModel = ref('best.pt')
const confidence = ref(0.25)
const iouThreshold = ref(0.45)

const imageFile = ref<File | null>(null)
const imageUrl = ref('')
const imageLoading = ref(false)
const detectProgress = ref(0)
const detections = ref<Detection[]>([])
const detectionStats = ref<DetectionStats>({})
const canvas = ref<HTMLCanvasElement | null>(null)
const resultImage = ref<HTMLImageElement | null>(null)
const originalZoom = ref(1)
const resultZoom = ref(1)
const originalPosition = ref({ x: 0, y: 0 })
const resultPosition = ref({ x: 0, y: 0 })
const isDragging = ref({ original: false, result: false })
const dragStart = ref({ x: 0, y: 0 })

const getTotalDetections = () => {
  return Object.values(detectionStats.value).reduce((a, b) => Number(a) + Number(b), 0)
}

const statsTableData = computed<StatsTableRow[]>(() => {
  const total = getTotalDetections()
  if (total === 0) return []
  
  return Object.entries(detectionStats.value).map(([name, count]): StatsTableRow => ({
    name,
    count: Number(count),
    percentage: Number(((Number(count) / total) * 100).toFixed(1))
  }))
})

const percentageFormat = (percentage: number) => `${percentage}%`
const formatProgress = (percentage: number) => `${percentage.toFixed(2)}%`

const exportStats = () => {
  const timestamp = new Date().toLocaleString().replace(/[/:\\]/g, '-')
  const csv = [
    ['品种', '数量', '占比'],
    ...statsTableData.value.map(row => [row.name, row.count, `${row.percentage}%`])
  ].map(row => row.join(',')).join('\n')
  
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `检测统计_${timestamp}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}

const handleImageChange = (file: UploadFile) => {
  imageFile.value = file.raw as File
  imageUrl.value = URL.createObjectURL(file.raw as File)
  detections.value = []
}

const uploadImage = async () => {
  if (!imageFile.value) return

  imageLoading.value = true
  detectProgress.value = 0
  const formData = new FormData()
  formData.append('file', imageFile.value)
  
  // 获取当前登录用户ID
  const userId = localStorage.getItem('userId') || '0'

  let progressTimer: number | undefined
  
  try {
    progressTimer = window.setInterval(() => {
      if (detectProgress.value < 90) {
        detectProgress.value = Number((detectProgress.value + Math.random() * 10).toFixed(2))
      }
    }, 200)

    const response = await axios.post(
      `/api/detect?model=${selectedModel.value}&conf=${confidence.value}&iou=${iouThreshold.value}&mode=image&user_id=${userId}`, 
      formData
    )
    
    if (!response.data) {
      throw new Error('服务器无响应')
    }
    
    if (!Array.isArray(response.data.detections)) {
      throw new Error('检测结果格式无效')
    }

    detections.value = response.data.detections
    
    const newStats: DetectionStats = {}
    detections.value.forEach((det: Detection) => {
      const currentCount = newStats[det.class_name] || 0
      newStats[det.class_name] = currentCount + 1
    })
    detectionStats.value = newStats
    
    if (response.data.history) {
      const historyRecord = {
        ...response.data.history,
        confidence: confidence.value,
        iou: iouThreshold.value
      }
      emit('detection-complete', historyRecord)
    }

    detectProgress.value = 100
  } catch (error) {
    console.error('Error uploading image:', error)
    ElMessage.error('图片检测失败')
    detections.value = []
    detectionStats.value = {}
  } finally {
    if (progressTimer !== undefined) {
      window.clearInterval(progressTimer)
    }
    
    setTimeout(() => {
      imageLoading.value = false
      detectProgress.value = 0
    }, 500)
  }
}

const drawDetections = () => {
  if (!canvas.value || !resultImage.value) return

  const img = resultImage.value
  canvas.value.width = img.naturalWidth
  canvas.value.height = img.naturalHeight

  const ctx = canvas.value.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)

  detections.value.forEach((det: Detection) => {
    const isEmpty = det.class_name.toLowerCase().includes('empty')
    ctx.strokeStyle = isEmpty ? '#ef4444' : '#22c55e'
    ctx.lineWidth = 3

    const x = Math.round(det.x1)
    const y = Math.round(det.y1)
    const width = Math.round(det.x2 - det.x1)
    const height = Math.round(det.y2 - det.y1)
    ctx.strokeRect(x, y, width, height)

    const label = `${det.class_name} ${det.confidence.toFixed(2)}`
    ctx.font = 'bold 16px Inter'
    const textMetrics = ctx.measureText(label)
    const textWidth = textMetrics.width
    const textHeight = 24
    ctx.fillStyle = isEmpty ? '#ef4444' : '#22c55e'
    ctx.fillRect(x, y - textHeight, textWidth + 10, textHeight)
    
    ctx.fillStyle = '#ffffff'
    ctx.fillText(label, x + 5, y - 6)
  })
}

const zoomIn = (type: 'original' | 'result') => {
  if (type === 'original') {
    originalZoom.value = Math.min(originalZoom.value + 0.2, 3)
  } else {
    resultZoom.value = Math.min(resultZoom.value + 0.2, 3)
  }
}

const zoomOut = (type: 'original' | 'result') => {
  if (type === 'original') {
    originalZoom.value = Math.max(originalZoom.value - 0.2, 0.5)
  } else {
    resultZoom.value = Math.max(resultZoom.value - 0.2, 0.5)
  }
}

const resetZoom = (type: 'original' | 'result') => {
  if (type === 'original') {
    originalZoom.value = 1
    originalPosition.value = { x: 0, y: 0 }
  } else {
    resultZoom.value = 1
    resultPosition.value = { x: 0, y: 0 }
  }
}

const handleWheel = (event: WheelEvent, type: 'original' | 'result') => {
  if (event.deltaY < 0) {
    zoomIn(type)
  } else {
    zoomOut(type)
  }
}

const startDrag = (event: MouseEvent, type: 'original' | 'result') => {
  isDragging.value[type] = true
  dragStart.value = {
    x: event.clientX - (type === 'original' ? originalPosition.value.x : resultPosition.value.x),
    y: event.clientY - (type === 'original' ? originalPosition.value.y : resultPosition.value.y)
  }
}

const onDrag = (event: MouseEvent, type: 'original' | 'result') => {
  if (!isDragging.value[type]) return
  
  const newX = event.clientX - dragStart.value.x
  const newY = event.clientY - dragStart.value.y
  
  if (type === 'original') {
    originalPosition.value = { x: newX, y: newY }
  } else {
    resultPosition.value = { x: newX, y: newY }
  }
}

const endDrag = (type: 'original' | 'result') => {
  isDragging.value[type] = false
}

const downloadResult = () => {
  if (!canvas.value) return
  
  const link = document.createElement('a')
  link.download = `detection_result_${new Date().getTime()}.png`
  link.href = canvas.value.toDataURL('image/png')
  link.click()
  ElMessage.success('图片已下载')
}
</script>

<style scoped>
.upload-container {
  display: flex;
  gap: 20px;
  justify-content: center;
  align-items: center;
  padding: 40px;
  margin-bottom: 30px;
  border: 1px dashed var(--primary-color);
  background: rgba(255, 255, 255, 0.5);
}

.custom-select {
  width: 200px;
}

.action-button {
  height: 40px;
  padding: 0 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.threshold-container {
  margin-bottom: 30px;
}

.threshold-card {
  padding: 24px;
}

.threshold-item {
  margin-bottom: 24px;
}

.threshold-item:last-child {
  margin-bottom: 0;
}

.threshold-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.threshold-label span {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: var(--text-primary);
}

.help-icon {
  color: var(--text-secondary);
  cursor: help;
  transition: color 0.3s;
}

.help-icon:hover {
  color: var(--primary-color);
}

.progress-container {
  padding: 30px;
  margin-bottom: 30px;
  text-align: center;
}

.progress-text {
  margin-top: 16px;
  color: var(--text-secondary);
  font-weight: 500;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 16px;
  padding-left: 12px;
  border-left: 4px solid var(--primary-color);
}

.stats-card {
  padding: 0;
  overflow: hidden;
}

.stats-header {
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}

.total-count {
  display: flex;
  flex-direction: column;
}

.total-count .label {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.total-count .value {
  font-size: 24px;
  font-weight: 800;
  color: var(--primary-color);
}

.custom-table {
  background: transparent !important;
}

.custom-table :deep(th) {
  background: rgba(249, 250, 251, 0.5) !important;
  font-weight: 600;
  color: var(--text-secondary);
}

.custom-table :deep(tr) {
  background: transparent !important;
}

.custom-table :deep(td) {
  background: transparent !important;
}

.preview-container {
  display: flex;
  gap: 24px;
  margin-top: 30px;
  flex-wrap: wrap;
}

.image-wrapper {
  flex: 1;
  min-width: 400px;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.image-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.image-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.ml-2 {
  margin-left: 8px;
}

.image-zoom-container {
  flex: 1;
  min-height: 400px;
  background: rgba(243, 244, 246, 0.5);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  border: 1px solid rgba(0,0,0,0.05);
}

.image-zoom-container:active {
  cursor: grabbing;
}

.image-zoom-container img {
  max-width: 100%;
  max-height: 100%;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.canvas-container {
  position: relative;
}

.detection-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
</style>
