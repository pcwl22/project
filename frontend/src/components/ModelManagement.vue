<template>
  <div class="model-management">
    <el-card class="model-card">
      <template #header>
        <div class="card-header">
          <span>上传模型权重</span>
        </div>
      </template>
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
        
        <div v-if="modelFile" class="model-info">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="文件名">
              {{ modelFile.name }}
            </el-descriptions-item>
            <el-descriptions-item label="文件大小">
              {{ formatFileSize(modelFile.size) }}
            </el-descriptions-item>
          </el-descriptions>
          
          <el-button 
            type="primary" 
            @click="uploadModel"
            :loading="modelUploading"
            style="margin-top: 20px; width: 100%;"
          >
            上传模型
          </el-button>
        </div>
      </div>
    </el-card>
    
    <el-card class="model-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>当前模型</span>
        </div>
      </template>
      <div class="current-model">
        <el-alert
          title="当前使用的模型权重文件"
          type="info"
          :closable="false"
        >
          <p>{{ currentModel || '默认模型' }}</p>
        </el-alert>
      </div>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

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
  formData.append('model', modelFile.value)

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
    ElMessage.error('模型上传失败')
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
}

.model-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.model-card:hover {
  box-shadow: 0 8px 30px rgba(102, 126, 234, 0.15);
  transform: translateY(-3px);
}

.card-header {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.model-upload-section {
  padding: 20px 0;
}

.model-upload {
  margin-bottom: 20px;
}

:deep(.el-upload-dragger) {
  border: 2px dashed #667eea;
  border-radius: 12px;
  background: linear-gradient(135deg, #f8f9ff 0%, #faf5ff 100%);
  transition: all 0.3s ease;
}

:deep(.el-upload-dragger:hover) {
  border-color: #764ba2;
  background: linear-gradient(135deg, #f0f1ff 0%, #f5ebff 100%);
}

:deep(.el-icon--upload) {
  font-size: 67px;
  color: #667eea;
  margin-bottom: 16px;
}

:deep(.el-upload__text) {
  color: #606266;
  font-size: 14px;
}

:deep(.el-upload__text em) {
  color: #667eea;
  font-style: normal;
}

:deep(.el-upload__tip) {
  color: #909399;
  font-size: 12px;
  margin-top: 10px;
}

.model-info {
  margin-top: 20px;
  padding: 20px;
  background: #f8f9ff;
  border-radius: 8px;
}

.current-model {
  padding: 10px 0;
}

:deep(.el-alert) {
  border-radius: 8px;
}

:deep(.el-descriptions) {
  border-radius: 8px;
}
</style>
