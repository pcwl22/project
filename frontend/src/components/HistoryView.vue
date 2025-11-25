<template>
  <div class="history-view">
    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <span>检测历史记录</span>
          <el-button type="danger" size="small" @click="clearHistory" :disabled="!historyList.length">
            清空历史
          </el-button>
        </div>
      </template>
      
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else-if="!historyList.length" class="empty-container">
        <el-empty description="暂无检测历史记录" />
      </div>
      
      <el-table v-else :data="historyList" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="image_path" label="图片名称" width="200">
          <template #default="scope">
            {{ getFileName(scope.row.image_path) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="检测时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="detection_count" label="检测数量" width="100" />
        <el-table-column label="检测结果" width="150">
          <template #default="scope">
            <el-tag v-for="(count, name) in scope.row.stats" :key="name" size="small" style="margin: 2px;">
              {{ name }}: {{ count }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="viewDetail(scope.row)">
              查看详情
            </el-button>
            <el-button size="small" type="danger" @click="deleteRecord(scope.row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-if="total > pageSize"
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        style="margin-top: 20px; justify-content: center;"
      />
    </el-card>
    
    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="检测详情" width="80%" :close-on-click-modal="false">
      <div v-if="currentRecord" class="detail-container">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="检测ID">{{ currentRecord.id }}</el-descriptions-item>
          <el-descriptions-item label="图片名称">{{ getFileName(currentRecord.image_path) }}</el-descriptions-item>
          <el-descriptions-item label="检测时间">{{ formatDate(currentRecord.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="检测数量">{{ currentRecord.detection_count }}</el-descriptions-item>
          <el-descriptions-item label="置信度阈值">
            <el-tag type="success">{{ currentRecord.confidence || 0.25 }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="IOU阈值">
            <el-tag type="info">{{ currentRecord.iou || 0.45 }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="images-container">
          <div class="result-image">
            <h4>原始图片</h4>
            <el-image
              :src="getImageUrl(currentRecord.id, 'original')"
              fit="contain"
              :preview-src-list="[getImageUrl(currentRecord.id, 'original')]"
              style="max-width: 100%; max-height: 500px;"
            />
          </div>
          <div class="result-image">
            <h4>检测结果图片</h4>
            <el-image
              :src="getImageUrl(currentRecord.id, 'result')"
              fit="contain"
              :preview-src-list="[getImageUrl(currentRecord.id, 'result')]"
              style="max-width: 100%; max-height: 500px;"
            />
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

interface HistoryRecord {
  id: number
  image_path: string
  saved_image_path: string
  created_at: string
  detection_count: number
  stats: { [key: string]: number }
  confidence?: number
  iou?: number
}

const historyList = ref<HistoryRecord[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const detailVisible = ref(false)
const currentRecord = ref<HistoryRecord | null>(null)

const fetchHistory = async () => {
  loading.value = true
  try {
    const userId = localStorage.getItem('userId')
    const isAdmin = localStorage.getItem('isAdmin') === 'true'
    const response = await axios.get('http://localhost:8000/detections/', {
      params: {
        limit: pageSize.value,
        offset: (currentPage.value - 1) * pageSize.value,
        user_id: userId ? parseInt(userId) : undefined,
        is_admin: isAdmin
      }
    })
    historyList.value = response.data.items || []
    total.value = response.data.total || 0
  } catch (error) {
    console.error('Error fetching history:', error)
    ElMessage.error('获取历史记录失败')
  } finally {
    loading.value = false
  }
}

const handleDetectionComplete = async (record: any) => {
  // 检测完成后，重新获取历史记录
  await fetchHistory()
}

const getFileName = (path: string) => {
  return path.split(/[/\\]/).pop() || path
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const viewDetail = (record: HistoryRecord) => {
  currentRecord.value = record
  detailVisible.value = true
}

const deleteRecord = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这条记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const userId = localStorage.getItem('userId')
    const isAdmin = localStorage.getItem('isAdmin') === 'true'
    await axios.delete(`http://localhost:8000/detections/${id}`, {
      params: { 
        user_id: userId ? parseInt(userId) : undefined,
        is_admin: isAdmin
      }
    })
    ElMessage.success('删除成功')
    fetchHistory()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Error deleting record:', error)
      ElMessage.error('删除失败')
    }
  }
}

const clearHistory = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有历史记录吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    // 批量删除
    for (const record of historyList.value) {
      await axios.delete(`http://localhost:8000/detections/${record.id}`)
    }
    
    ElMessage.success('清空成功')
    fetchHistory()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Error clearing history:', error)
      ElMessage.error('清空失败')
    }
  }
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchHistory()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchHistory()
}

const getImageUrl = (recordId: number, type: 'original' | 'result') => {
  const userId = localStorage.getItem('userId')
  const isAdmin = localStorage.getItem('isAdmin') === 'true'
  const params = new URLSearchParams()
  if (userId) params.append('user_id', userId)
  if (isAdmin) params.append('is_admin', 'true')
  const queryString = params.toString()
  return `http://localhost:8000/detections/${recordId}/${type}${queryString ? '?' + queryString : ''}`
}

onMounted(() => {
  fetchHistory()
})

defineExpose({
  fetchHistory,
  handleDetectionComplete
})
</script>

<style scoped>
.history-view {
  padding: 20px;
}

.history-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.loading-container,
.empty-container {
  padding: 40px 0;
}

:deep(.el-table) {
  border-radius: 8px;
}

:deep(.el-table th) {
  background: #f8f9ff;
  color: #2c3e50;
  font-weight: 600;
}

:deep(.el-table tr) {
  transition: all 0.3s ease;
}

:deep(.el-table tbody tr:hover) {
  background: linear-gradient(90deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05)) !important;
}

.detail-container {
  padding: 20px 0;
}

.images-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 20px;
}

.result-image {
  text-align: center;
}

.result-image h4 {
  margin-bottom: 15px;
  color: #2c3e50;
}

@media (max-width: 768px) {
  .images-container {
    grid-template-columns: 1fr;
  }
}

:deep(.el-pagination) {
  display: flex;
  justify-content: center;
}
</style>
