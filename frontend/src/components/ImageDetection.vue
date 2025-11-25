<template>
  <div class="upload-container">
    <el-select 
      v-model="selectedModel" 
      placeholder="选择模型权重"
      size="large"
      style="width: 200px;"
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
        <el-button type="primary">选择图片</el-button>
      </template>
    </el-upload>
    
    <el-button
      type="success" 
      @click="uploadImage"
      :disabled="!imageFile"
      :loading="imageLoading"
    >
      开始检测
    </el-button>
  </div>
  
  <!-- 置信度和 IOU 阈值设置 -->
  <div class="threshold-container">
    <el-card class="threshold-card">
      <div class="threshold-item">
        <div class="threshold-label">
          <span>
            置信度阈值
            <el-tooltip content="控制检测结果的最低置信度，值越高，过滤越严格，误检越少" placement="top">
              <el-icon style="margin-left: 5px; cursor: help;"><QuestionFilled /></el-icon>
            </el-tooltip>
          </span>
          <el-tag size="small">{{ confidence }}</el-tag>
        </div>
        <el-slider 
          v-model="confidence" 
          :min="0" 
          :max="1" 
          :step="0.05"
          show-stops
        />
      </div>
      <div class="threshold-item">
        <div class="threshold-label">
          <span>
            IOU 阈值
            <el-tooltip content="非极大值抑制阈值，控制重叠框的过滤，值越小，过滤越严格" placement="top">
              <el-icon style="margin-left: 5px; cursor: help;"><QuestionFilled /></el-icon>
            </el-tooltip>
          </span>
          <el-tag size="small">{{ iouThreshold }}</el-tag>
        </div>
        <el-slider 
          v-model="iouThreshold" 
          :min="0" 
          :max="1" 
          :step="0.05"
          show-stops
        />
      </div>
    </el-card>
  </div>

  <!-- 检测进度条 -->
  <div v-if="imageLoading" class="progress-container">
    <el-progress 
      :percentage="detectProgress" 
      :format="formatProgress"
      :duration="5"
    />
    <p class="progress-text">正在检测中...</p>
  </div>

  <!-- 检测统计信息 -->
  <div v-if="detections.length" class="stats-container">
    <h3>检测统计</h3>
    <el-card>
      <template #header>
        <div class="stats-header">
          <span>总数量: {{ getTotalDetections() }}</span>
          <el-button type="primary" link @click="exportStats">导出统计</el-button>
        </div>
      </template>
      <el-table :data="statsTableData" stripe>
        <el-table-column prop="name" label="品种" />
        <el-table-column prop="count" label="数量" />
        <el-table-column prop="percentage" label="占比">
          <template #default="scope">
            <el-progress :percentage="scope.row.percentage" :format="percentageFormat" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>

  <div class="preview-container" v-if="imageUrl">
    <div class="image-wrapper">
      <div class="image-header">
        <h3>原始图片</h3>
        <el-button-group>
          <el-button size="small" @click="zoomIn('original')" icon="ZoomIn"></el-button>
          <el-button size="small" @click="zoomOut('original')" icon="ZoomOut"></el-button>
          <el-button size="small" @click="resetZoom('original')" icon="RefreshRight"></el-button>
        </el-button-group>
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
    <div class="image-wrapper" v-if="detections.length">
      <div class="image-header">
        <h3>检测结果</h3>
        <el-button-group>
          <el-button size="small" @click="zoomIn('result')" icon="ZoomIn"></el-button>
          <el-button size="small" @click="zoomOut('result')" icon="ZoomOut"></el-button>
          <el-button size="small" @click="resetZoom('result')" icon="RefreshRight"></el-button>
          <el-button size="small" @click="downloadResult" icon="Download">下载</el-button>
        </el-button-group>
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
import { QuestionFilled, ZoomIn, ZoomOut, RefreshRight, Download } from '@element-plus/icons-vue'

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
  formData.append('mode', 'image')
  if (props.currentUserId) {
    formData.append('user_id', props.currentUserId.toString())
  }

  let progressTimer: number | undefined
  
  try {
    progressTimer = window.setInterval(() => {
      if (detectProgress.value < 90) {
        detectProgress.value = Number((detectProgress.value + Math.random() * 10).toFixed(2))
      }
    }, 200)

    const response = await axios.post(
      `http://localhost:8000/detect?model=${selectedModel.value}&conf=${confidence.value}&iou=${iouThreshold.value}`, 
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
    ctx.strokeStyle = isEmpty ? '#ff0000' : '#00ff00'
    ctx.lineWidth = 2

    const x = Math.round(det.x1)
    const y = Math.round(det.y1)
    const width = Math.round(det.x2 - det.x1)
    const height = Math.round(det.y2 - det.y1)
    ctx.strokeRect(x, y, width, height)

    const label = `${det.class_name} ${det.confidence.toFixed(2)}`
    ctx.font = '16px Arial'
    const textMetrics = ctx.measureText(label)
    const textWidth = textMetrics.width
    const textHeight = 20
    ctx.fillStyle = isEmpty ? '#ff0000' : '#00ff00'
    ctx.fillRect(x, y - textHeight, textWidth + 6, textHeight)
    
    ctx.fillStyle = '#ffffff'
    ctx.fillText(label, x + 3, y - 4)
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
  margin-bottom: 30px;
  padding: 30px;
  background: linear-gradient(135deg, #f8f9ff 0%, #faf5ff 100%);
  border-radius: 12px;
  border: 2px dashed #667eea;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.upload-container::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(102, 126, 234, 0.1), transparent);
  transform: rotate(45deg);
  transition: all 0.6s;
}

.upload-container:hover::before {
  left: 100%;
}

.upload-container:hover {
  border-color: #764ba2;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
  transform: translateY(-2px);
}

.preview-container {
  display: flex;
  gap: 30px;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 30px;
}

.image-wrapper {
  flex: 1;
  min-width: 300px;
  max-width: 600px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.image-wrapper:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(102, 126, 234, 0.2);
}

.image-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 2px solid #f0f0f0;
}

.image-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
  position: relative;
  padding-bottom: 5px;
}

.image-header h3::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 40px;
  height: 3px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.image-wrapper:hover .image-header h3::after {
  width: 80px;
}

.image-zoom-container {
  overflow: hidden;
  cursor: grab;
  position: relative;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  border-radius: 8px;
  user-select: none;
}

.image-zoom-container:active {
  cursor: grabbing;
}

.image-wrapper img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
}

.canvas-container {
  position: relative;
  display: inline-block;
  transform-origin: center center;
}

.canvas-container img {
  max-width: 100%;
  height: auto;
  display: block;
  border-radius: 8px;
}

.detection-canvas {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.progress-container {
  margin: 30px auto;
  max-width: 600px;
  text-align: center;
  padding: 30px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  }
  50% {
    box-shadow: 0 4px 30px rgba(102, 126, 234, 0.2);
  }
}

.progress-text {
  margin-top: 15px;
  color: #666;
  font-size: 16px;
  font-weight: 500;
}

.stats-container {
  margin: 30px auto;
  max-width: 900px;
  animation: slideInUp 0.6s ease-out;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stats-container h3 {
  margin-bottom: 20px;
  color: #2c3e50;
  font-size: 20px;
  font-weight: 600;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 5px;
}

/* Threshold styles */
.threshold-container {
  margin: 20px 0;
}

.threshold-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  animation: slideInLeft 0.6s ease-out;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.threshold-card:hover {
  box-shadow: 0 8px 30px rgba(102, 126, 234, 0.15);
  transform: translateY(-2px);
}

.threshold-item {
  margin-bottom: 20px;
}

.threshold-item:last-child {
  margin-bottom: 0;
}

.threshold-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.threshold-label span {
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
}
</style>
