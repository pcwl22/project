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
      :on-change="handleVideoChange"
      accept="video/*"
    >
      <template #trigger>
        <el-button type="primary">选择视频</el-button>
      </template>
    </el-upload>
    
    <el-button 
      type="success" 
      @click="uploadVideo"
      :disabled="!videoFile"
      :loading="videoLoading"
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

  <div class="preview-container" v-if="videoUrl || resultVideoUrl">
    <div class="video-wrapper">
      <h3>原始视频</h3>
      <video :src="videoUrl" controls v-if="videoUrl"></video>
    </div>
    <div class="video-wrapper" v-if="resultVideoUrl">
      <h3>检测结果</h3>
      <video :src="resultVideoUrl" controls></video>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { QuestionFilled } from '@element-plus/icons-vue'

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

const uploadVideo = async () => {
  if (!videoFile.value) return

  videoLoading.value = true
  const formData = new FormData()
  formData.append('file', videoFile.value)
  formData.append('mode', 'video')

  try {
    const response = await axios.post('/api/detect', formData, {
      responseType: 'blob'
    })

    const videoBlob = new Blob([response.data], { type: 'video/mp4' })
    resultVideoUrl.value = URL.createObjectURL(videoBlob)

    emit('detection-complete')
  } catch (error) {
    console.error('Error uploading video:', error)
    ElMessage.error('视频检测失败')
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

.video-wrapper {
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

.video-wrapper:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(102, 126, 234, 0.2);
}

.video-wrapper h3 {
  margin: 0 0 15px 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
  position: relative;
  padding-bottom: 5px;
  border-bottom: 2px solid #f0f0f0;
}

.video-wrapper h3::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 40px;
  height: 3px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.video-wrapper:hover h3::after {
  width: 80px;
}

.video-wrapper video {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
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
