<template>
  <div class="algorithm-settings">
    <el-card class="settings-card glass-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Setting /></el-icon>
            <span>空货架检测算法设置</span>
          </div>
          <el-switch
            v-model="config.enable_empty_detection"
            @change="updateConfig"
            active-text="启用"
            inactive-text="禁用"
            size="large"
          />
        </div>
      </template>

      <div class="settings-content" v-loading="loading">
        <!-- 提示信息：当检测功能关闭时 -->
        <el-alert
          v-if="!config.enable_empty_detection"
          title="空货架检测已禁用"
          type="warning"
          :closable="false"
          class="disabled-tip"
          show-icon
        >
          <template #default>
            <div>
              请先开启空货架检测功能，才能调整算法参数
            </div>
          </template>
        </el-alert>

        <!-- 算法参数设置：只在检测功能开启时显示 -->
        <el-collapse v-if="config.enable_empty_detection" v-model="activeNames" class="custom-collapse">
          <!-- 基础参数 -->
          <el-collapse-item title="基础参数" name="basic">
            <div class="param-group">
              <!-- 间隙阈值 -->
              <div class="param-item">
                <div class="param-header">
                  <span class="param-label">
                    间隙阈值
                    <el-tooltip placement="top">
                      <template #content>
                        <div style="max-width: 300px;">
                          控制多大的间隙被识别为空货架<br/>
                          值越大，需要更大的间隙才会被识别<br/>
                          建议范围：0.3 - 0.8
                        </div>
                      </template>
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                  <el-tag size="small" effect="dark">{{ config.gap_threshold }}</el-tag>
                </div>
                <el-slider
                  v-model="config.gap_threshold"
                  :min="0.1"
                  :max="2.0"
                  :step="0.1"
                  @change="updateConfig"
                  show-stops
                  :marks="{ 0.3: '0.3', 0.5: '0.5', 0.8: '0.8', 1.0: '1.0' }"
                />
              </div>

              <!-- 行聚类阈值 -->
              <div class="param-item">
                <div class="param-header">
                  <span class="param-label">
                    行聚类阈值
                    <el-tooltip placement="top">
                      <template #content>
                        <div style="max-width: 300px;">
                          控制商品如何分组到同一行<br/>
                          值越大，垂直距离更远的商品也会被分到同一行<br/>
                          建议范围：0.4 - 0.8
                        </div>
                      </template>
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                  <el-tag size="small" effect="dark">{{ config.row_threshold }}</el-tag>
                </div>
                <el-slider
                  v-model="config.row_threshold"
                  :min="0.1"
                  :max="2.0"
                  :step="0.1"
                  @change="updateConfig"
                  show-stops
                  :marks="{ 0.4: '0.4', 0.6: '0.6', 0.8: '0.8' }"
                />
              </div>

              <!-- 最小间隙像素 -->
              <div class="param-item">
                <div class="param-header">
                  <span class="param-label">
                    最小间隙像素
                    <el-tooltip placement="top">
                      <template #content>
                        <div style="max-width: 300px;">
                          间隙的最小像素数<br/>
                          小于此值的间隙会被忽略<br/>
                          建议范围：15 - 30
                        </div>
                      </template>
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                  <el-tag size="small" effect="dark">{{ config.min_gap_pixels }} px</el-tag>
                </div>
                <el-slider
                  v-model="config.min_gap_pixels"
                  :min="5"
                  :max="100"
                  :step="5"
                  @change="updateConfig"
                  show-stops
                  :marks="{ 15: '15', 20: '20', 30: '30' }"
                />
              </div>
            </div>
          </el-collapse-item>

          <!-- 高级参数 -->
          <el-collapse-item title="高级参数" name="advanced">
            <div class="param-group">
              <!-- 边缘检测 -->
              <div class="param-item">
                <div class="param-header">
                  <span class="param-label">
                    货架边缘空位检测
                    <el-tooltip placement="top">
                      <template #content>
                        <div style="max-width: 300px;">
                          是否检测货架左右两侧的空位<br/>
                          启用后会检测货架边缘的空白区域
                        </div>
                      </template>
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                  <el-switch
                    v-model="config.edge_detection"
                    @change="updateConfig"
                  />
                </div>
              </div>

              <!-- 每行最少商品数 -->
              <div class="param-item">
                <div class="param-header">
                  <span class="param-label">
                    每行最少商品数
                    <el-tooltip placement="top">
                      <template #content>
                        <div style="max-width: 300px;">
                          只有商品数达到此值的行才会进行空位检测<br/>
                          避免在商品稀少的行产生误检<br/>
                          建议值：2
                        </div>
                      </template>
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                  <el-tag size="small" effect="dark">{{ config.min_products_per_row }}</el-tag>
                </div>
                <el-slider
                  v-model="config.min_products_per_row"
                  :min="1"
                  :max="10"
                  :step="1"
                  @change="updateConfig"
                  show-stops
                  :marks="{ 1: '1', 2: '2', 3: '3', 5: '5' }"
                />
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>

        <!-- 操作按钮：只在检测功能开启时显示 -->
        <div v-if="config.enable_empty_detection" class="actions">
          <el-button @click="resetConfig" :loading="loading">
            <el-icon><RefreshLeft /></el-icon>
            恢复默认
          </el-button>
          <el-button type="primary" @click="loadConfig" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新配置
          </el-button>
        </div>

        <!-- 配置说明：只在检测功能开启时显示 -->
        <el-alert
          v-if="config.enable_empty_detection"
          title="提示"
          type="info"
          :closable="false"
          class="config-tip"
        >
          <template #default>
            <div>
              • 所有参数修改后立即生效，无需重启服务<br/>
              • 建议先使用默认参数，根据实际效果调整<br/>
              • 参数调整后可以重新检测图片查看效果
            </div>
          </template>
        </el-alert>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Setting, QuestionFilled, RefreshLeft, Refresh } from '@element-plus/icons-vue'

interface AlgorithmConfig {
  enable_empty_detection: boolean
  gap_threshold: number
  row_threshold: number
  min_gap_pixels: number
  edge_detection: boolean
  min_products_per_row: number
}

const loading = ref(false)
const activeNames = ref(['basic', 'advanced'])

const config = ref<AlgorithmConfig>({
  enable_empty_detection: true,
  gap_threshold: 0.5,
  row_threshold: 0.6,
  min_gap_pixels: 20,
  edge_detection: true,
  min_products_per_row: 2
})

// 加载配置
const loadConfig = async () => {
  loading.value = true
  try {
    const response = await axios.get('http://localhost:8000/api/config/detection')
    config.value = response.data
    ElMessage.success('配置加载成功')
  } catch (error) {
    console.error('Failed to load config:', error)
    ElMessage.error('配置加载失败')
  } finally {
    loading.value = false
  }
}

// 更新配置
const updateConfig = async () => {
  loading.value = true
  try {
    const response = await axios.put('http://localhost:8000/api/config/detection', config.value)
    if (response.data.success) {
      ElMessage.success('配置已更新')
    } else {
      ElMessage.error(response.data.message || '配置更新失败')
      // 失败时重新加载配置
      await loadConfig()
    }
  } catch (error) {
    console.error('Failed to update config:', error)
    ElMessage.error('配置更新失败')
    // 失败时重新加载配置
    await loadConfig()
  } finally {
    loading.value = false
  }
}

// 重置配置
const resetConfig = async () => {
  loading.value = true
  try {
    const response = await axios.post('http://localhost:8000/api/config/detection/reset')
    if (response.data.success) {
      config.value = response.data.current_config
      ElMessage.success('配置已重置为默认值')
    } else {
      ElMessage.error('配置重置失败')
    }
  } catch (error) {
    console.error('Failed to reset config:', error)
    ElMessage.error('配置重置失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.algorithm-settings {
  padding: 20px;
}

.settings-card {
  max-width: 800px;
  margin: 0 auto;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  font-size: 24px;
  color: var(--el-color-primary);
}

.settings-content {
  padding: 10px 0;
}

.custom-collapse {
  border: none;
}

.custom-collapse :deep(.el-collapse-item__header) {
  font-size: 16px;
  font-weight: 500;
  padding: 15px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.custom-collapse :deep(.el-collapse-item__content) {
  padding: 20px 0;
}

.param-group {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.param-item .param-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.param-item .param-header .param-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.param-item .param-header .help-icon {
  color: var(--el-color-info);
  cursor: help;
  font-size: 16px;
}

.param-item .param-header .help-icon:hover {
  color: var(--el-color-primary);
}

.param-item :deep(.el-slider) {
  padding: 0 10px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin: 30px 0 20px;
}

.config-tip {
  margin-top: 20px;
}

.config-tip :deep(.el-alert__content) {
  line-height: 1.8;
}

.disabled-tip {
  margin-bottom: 20px;
}

.disabled-tip :deep(.el-alert__content) {
  font-size: 14px;
}

.glass-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}
</style>
