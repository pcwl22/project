<template>
  <div class="user-management">
    <el-card class="user-card">
      <template #header>
        <div class="card-header">
          <span>用户列表</span>
          <el-button type="primary" size="small" @click="loadUsers">刷新</el-button>
        </div>
      </template>
      <el-table :data="userList" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="200" />
        <el-table-column prop="is_admin" label="管理员" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_admin ? 'danger' : 'info'">
              {{ scope.row.is_admin ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detection_count" label="检测次数" width="120" />
        <el-table-column prop="created_at" label="注册时间" width="180" />
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button
              size="small"
              type="danger"
              @click="deleteUser(scope.row.id)"
              :disabled="scope.row.is_admin"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  isAdmin: boolean
}>()

const userList = ref<any[]>([])

const loadUsers = async () => {
  if (!props.isAdmin) return
  
  try {
    const response = await axios.get('http://localhost:8000/admin/users', {
      params: { is_admin: true }
    })
    userList.value = response.data
  } catch (error) {
    console.error('Error loading users:', error)
    ElMessage.error('加载用户列表失败')
  }
}

const deleteUser = async (userId: number) => {
  try {
    await axios.delete(`http://localhost:8000/admin/users/${userId}`, {
      params: { is_admin: true }
    })
    ElMessage.success('用户已删除')
    loadUsers()
  } catch (error: any) {
    console.error('Error deleting user:', error)
    const msg = error.response?.data?.detail || '删除用户失败'
    ElMessage.error(msg)
  }
}

onMounted(() => {
  if (props.isAdmin) {
    loadUsers()
  }
})
</script>

<style scoped>
.user-management {
  /* max-width: 1000px; */
  /* margin: 0 auto; */
}

.user-card {
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

:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
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
  transform: scale(1.005);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}
</style>
