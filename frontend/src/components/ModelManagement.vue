<template>
  <div class="model-management">
    <div class="model-card glass-card">
      <div class="card-header">
        <div class="header-icon">
          <el-icon><UploadFilled /></el-icon>
        </div>
        <span>上传模型权重</span>
      </div>
      <div class="model-upload-section">
        <el-upload
          class="model-upload"
          drag
          action="#"
          :auto-upload="false"
          :on-change="handleModelChange"
          :show-file-list="false"
          accept=".pt"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将模型文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .pt 格式的 YOLOv8 模型权重文件
            </div>
          </template>
        </el-upload>
        
        <div v-if="modelFile" class="model-info glass-card">
          <el-descriptions :column="1" border class="custom-descriptions">
            <el-descriptions-item label="文件名">
              <span class="info-text">{{ modelFile.name }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="文件大小">
              <span class="info-text">{{ formatFileSize(modelFile.size) }}</span>
            </el-descriptions-item>
          </el-descriptions>
          
          <el-button 
            type="primary" 
            @click="uploadModel"
            :loading="modelUploading"
            class="upload-btn"
          >
            <el-icon><Upload /></el-icon>
            上传模型
          </el-button>
        </div>
      </div>
    </div>
    
    <div class="model-card glass-card mt-6">
      <div class="card-header">
        <div class="header-icon">
          <el-icon><Cpu /></el-icon>
        </div>
        <span>当前模型</span>
      </div>
      <div class="current-model">
        <el-alert
          title="当前使用的模型权重文件"
          type="info"
          :closable="false"
          show-icon
          class="custom-alert"
        >
          <p class="current-model-name">{{ currentModel || '默认模型' }}</p>
        </el-alert>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { UploadFilled, Upload, Cpu } from '@element-plus/icons-vue'

const props = defineProps<{
  currentModel: string
  modelList: string[]
}>()

const emit = defineEmits<{
  (e: 'update:modelList', list: string[]): void
  (e: 'update:currentModel', model: string): void
}>()

const modelFile = ref<File | null>(null)
const modelUploading = ref(false)

const handleModelChange = (file: UploadFile) => {
  if (!file.raw) return
  
  // 检查文件类型
  if (!file.name.endsWith('.pt')) {
    ElMessage.error('请上传 .pt 格式的模型文件！')
    return
  }
  
  modelFile.value = file.raw as File
  ElMessage.success(`已选择模型：${file.name}`)
}

const uploadModel = async () => {
  if (!modelFile.value) return

  modelUploading.value = true
  const formData = new FormData()
  formData.append('file', modelFile.value)  // 修复：后端接收的参数名是 'file'

  try {
    await axios.post('http://localhost:8000/upload_model', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    ElMessage.success('模型上传成功！')
    emit('update:currentModel', modelFile.value.name)
    
    // 将新上传的模型添加到模型列表
    if (!props.modelList.includes(modelFile.value.name)) {
      const newList = [modelFile.value.name, ...props.modelList]
      emit('update:modelList', newList)
    }
    
    modelFile.value = null
  } catch (error) {
    console.error('Error uploading model:', error)
    ElMessage.error('模型上传失败，请检查后端服务是否正常运行')
  } finally {
    modelUploading.value = false
  }
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
.model-management {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.model-card {
  padding: 24px;
  margin-bottom: 24px;
}

.mt-6 {
  margin-top: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.header-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.model-upload-section {
  padding: 10px 0;
}

.model-upload {
  margin-bottom: 24px;
}

:deep(.el-upload-dragger) {
  border: 2px dashed rgba(99, 102, 241, 0.3);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.5);
  transition: all 0.3s ease;
  padding: 40px;
}

:deep(.el-upload-dragger:hover) {
  border-color: var(--primary-color);
  background: rgba(255, 255, 255, 0.8);
  transform: translateY(-2px);
}

:deep(.el-icon--upload) {
  font-size: 64px;
  color: var(--primary-color);
  margin-bottom: 16px;
  filter: drop-shadow(0 4px 8px rgba(99, 102, 241, 0.2));
}

:deep(.el-upload__text) {
  color: var(--text-secondary);
  font-size: 15px;
}

:deep(.el-upload__text em) {
  color: var(--primary-color);
  font-weight: 600;
  font-style: normal;
}

:deep(.el-upload__tip) {
  color: var(--text-secondary);
  font-size: 13px;
  margin-top: 12px;
  text-align: center;
}

.model-info {
  margin-top: 24px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.6);
}

.custom-descriptions :deep(.el-descriptions__cell) {
  background: transparent;
}

.info-text {
  font-weight: 500;
  color: var(--text-primary);
}

.upload-btn {
  margin-top: 20px;
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.current-model {
  padding: 10px 0;
}

.custom-alert {
  background: rgba(99, 102, 241, 0.05);
  border: 1px solid rgba(99, 102, 241, 0.1);
  padding: 16px;
}

.current-model-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-color);
  margin: 8px 0 0 0;
}
</style>
