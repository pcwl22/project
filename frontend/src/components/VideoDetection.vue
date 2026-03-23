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
      :on-change="handleVideoChange"
      accept="video/*"
    >
      <template #trigger>
        <el-button type="primary" class="action-button">
          <el-icon><VideoCamera /></el-icon>
          选择视频
        </el-button>
      </template>
    </el-upload>
    
    <el-button 
      type="success" 
      @click="uploadVideo"
      :disabled="!videoFile"
      :loading="videoLoading"
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

  <div class="preview-container" v-if="videoUrl || resultVideoUrl">
    <div class="video-wrapper glass-card">
      <div class="video-header">
        <h3>原始视频</h3>
      </div>
      <div class="video-content">
        <video 
          :src="videoUrl" 
          controls 
          v-if="videoUrl"
          @error="handleVideoError('original')"
          @loadeddata="handleVideoLoaded('original')"
        ></video>
      </div>
    </div>
    <div class="video-wrapper glass-card" v-if="resultVideoUrl">
      <div class="video-header">
        <h3>检测结果</h3>
        <el-button 
          size="small" 
          type="primary" 
          @click="downloadVideo"
          :icon="Download"
        >
          下载视频
        </el-button>
      </div>
      <div class="video-content">
        <video 
          :src="resultVideoUrl" 
          controls
          @error="handleVideoError('result')"
          @loadeddata="handleVideoLoaded('result')"
        ></video>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { QuestionFilled, VideoCamera, CaretRight, Download } from '@element-plus/icons-vue'

const props = defineProps<{
  modelList: string[]
}>()

const emit = defineEmits<{
  (e: 'detection-complete'): void
}>()

const selectedModel = ref('best.pt')
const confidence = ref(0.25)
const iouThreshold = ref(0.45)

const videoFile = ref<File | null>(null)
const videoUrl = ref('')
const resultVideoUrl = ref('')
const videoLoading = ref(false)

const handleVideoChange = (file: UploadFile) => {
  videoFile.value = file.raw as File
  videoUrl.value = URL.createObjectURL(file.raw as File)
  resultVideoUrl.value = ''
}

const handleVideoError = (type: string) => {
  console.error(`Video error (${type}):`, event)
  ElMessage.error(`${type === 'original' ? '原始' : '结果'}视频加载失败`)
}

const handleVideoLoaded = (type: string) => {
  console.log(`Video loaded (${type})`)
}

const downloadVideo = () => {
  if (!resultVideoUrl.value) return
  
  const link = document.createElement('a')
  link.href = resultVideoUrl.value
  link.download = `detected_${Date.now()}.mp4`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const uploadVideo = async () => {
  if (!videoFile.value) return

  videoLoading.value = true
  const formData = new FormData()
  formData.append('file', videoFile.value)

  try {
    const response = await axios.post(
      `/api/detect?mode=video&conf=${confidence.value}&iou=${iouThreshold.value}&model=${selectedModel.value}`,
      formData,
      {
        responseType: 'blob',
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 300000  // 5分钟超时
      }
    )

    console.log('Response received:', response)
    console.log('Response type:', response.headers['content-type'])
    console.log('Response size:', response.data.size)

    // 检查响应是否为视频
    if (!response.data || response.data.size === 0) {
      throw new Error('接收到空的视频文件')
    }

    // 创建 Blob URL
    const videoBlob = new Blob([response.data], { type: 'video/mp4' })
    const blobUrl = URL.createObjectURL(videoBlob)
    
    console.log('Blob URL created:', blobUrl)
    console.log('Blob size:', videoBlob.size)
    console.log('Blob type:', videoBlob.type)
    
    // 释放旧的 URL
    if (resultVideoUrl.value) {
      URL.revokeObjectURL(resultVideoUrl.value)
    }
    
    resultVideoUrl.value = blobUrl

    ElMessage.success('视频检测完成')
    emit('detection-complete')
  } catch (error: any) {
    console.error('Error uploading video:', error)
    if (error.code === 'ECONNABORTED') {
      ElMessage.error('视频处理超时，请尝试较短的视频')
    } else if (error.response) {
      ElMessage.error(`视频检测失败: ${error.response.status}`)
    } else {
      ElMessage.error('视频检测失败')
    }
  } finally {
    videoLoading.value = false
  }
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

.preview-container {
  display: flex;
  gap: 24px;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 30px;
}

.video-wrapper {
  flex: 1;
  min-width: 400px;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.video-header {
  margin-bottom: 16px;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  padding-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.video-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.video-content {
  flex: 1;
  background: black;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.video-wrapper video {
  max-width: 100%;
  max-height: 100%;
}
</style>
