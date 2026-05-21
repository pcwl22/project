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
        <el-table-column prop="file_type" label="类型" width="100">
          <template #default="scope">
            <el-tag 
              :type="scope.row.file_type === 'video' ? 'warning' : scope.row.file_type === 'camera' ? 'success' : 'info'" 
              size="small"
            >
              {{ scope.row.file_type === 'video' ? '视频' : scope.row.file_type === 'camera' ? '摄像头' : '图片' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="image_path" label="文件名称" width="200">
          <template #default="scope">
            {{ getFileName(scope.row.image_path) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="检测时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_detections" label="检测数量" width="150">
          <template #default="scope">
            <el-tag v-if="scope.row.file_type === 'video' || scope.row.file_type === 'camera'" type="info" size="small">
              点击查看详情
            </el-tag>
            <el-tag v-else type="success" size="small">
              总数: {{ scope.row.total_detections }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="检测详情" width="200">
          <template #default="scope">
            <div v-if="scope.row.file_type === 'video' || scope.row.file_type === 'camera'">
              <el-tag type="warning" size="small">
                空货架最大值: {{ scope.row.max_empty_count || 0 }}
              </el-tag>
            </div>
            <div v-else style="display: flex; gap: 5px; flex-wrap: wrap;">
              <el-tag type="primary" size="small">
                商品: {{ scope.row.product_count }}
              </el-tag>
              <el-tag type="danger" size="small" v-if="scope.row.empty_count > 0">
                空位: {{ scope.row.empty_count }}
              </el-tag>
            </div>
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
          <el-descriptions-item label="文件类型">
            <el-tag 
              :type="currentRecord.file_type === 'video' ? 'warning' : currentRecord.file_type === 'camera' ? 'success' : 'info'" 
              size="small"
            >
              {{ currentRecord.file_type === 'video' ? '视频' : currentRecord.file_type === 'camera' ? '摄像头' : '图片' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="文件名称">{{ getFileName(currentRecord.image_path) }}</el-descriptions-item>
          <el-descriptions-item label="检测时间">{{ formatDate(currentRecord.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="检测数量" v-if="currentRecord.file_type !== 'video' && currentRecord.file_type !== 'camera'">
            <el-tag type="success" size="small">总数: {{ currentRecord.total_detections || 0 }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="检测详情" v-if="currentRecord.file_type !== 'video' && currentRecord.file_type !== 'camera'">
            <div style="display: flex; gap: 8px;">
              <el-tag type="primary" size="small">商品: {{ currentRecord.product_count || 0 }}</el-tag>
              <el-tag type="danger" size="small" v-if="(currentRecord.empty_count || 0) > 0">
                空位: {{ currentRecord.empty_count }}
              </el-tag>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="空位率" v-if="currentRecord.file_type !== 'video' && currentRecord.file_type !== 'camera' && (currentRecord.empty_count || 0) > 0">
            <el-tag type="warning" size="small">
              {{ ((currentRecord.empty_rate || 0) * 100).toFixed(1) }}%
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 图片显示：只对图片类型显示 -->
        <div v-if="currentRecord.file_type !== 'video' && currentRecord.file_type !== 'camera'" class="images-container">
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
        
        <!-- 视频/摄像头提示：只对视频和摄像头类型显示 -->
        <el-alert
          v-if="currentRecord.file_type === 'video' || currentRecord.file_type === 'camera'"
          :title="currentRecord.file_type === 'video' ? '视频检测统计' : '摄像头检测统计'"
          type="success"
          :closable="false"
          style="margin-top: 20px;"
        >
          <template #default>
            <div>
              <strong>空货架最大值：{{ currentRecord.max_empty_count || 0 }}</strong><br/>
              {{ currentRecord.file_type === 'video' ? '视频' : '摄像头' }}检测已完成，检测结果已保存到本地。<br/>
              文件路径：{{ currentRecord.saved_image_path }}
            </div>
          </template>
        </el-alert>
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
  file_type: string
  created_at: string
  total_detections: number
  product_count: number
  empty_count: number
  empty_rate: number
  stats?: { [key: string]: number }
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
    const response = await axios.get('http://localhost:8000/api/detections/', {
      params: {
        limit: pageSize.value,
        skip: (currentPage.value - 1) * pageSize.value,
        user_id: userId ? parseInt(userId) : undefined,
        is_admin: isAdmin
      }
    })
    historyList.value = response.data.records || []
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

const viewDetail = async (record: HistoryRecord) => {
  try {
    // 从后端获取完整的详情数据
    const userId = localStorage.getItem('userId')
    const isAdmin = localStorage.getItem('isAdmin') === 'true'
    const response = await axios.get(`http://localhost:8000/api/detections/${record.id}`, {
      params: {
        user_id: userId ? parseInt(userId) : undefined,
        is_admin: isAdmin
      }
    })
    currentRecord.value = response.data
    detailVisible.value = true
  } catch (error) {
    console.error('Error fetching detail:', error)
    ElMessage.error('获取详情失败')
  }
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
    await axios.delete(`http://localhost:8000/api/detections/${id}`, {
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
      await axios.delete(`http://localhost:8000/api/detections/${record.id}`)
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
  return `http://localhost:8000/api/detections/${recordId}/${type}${queryString ? '?' + queryString : ''}`
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
