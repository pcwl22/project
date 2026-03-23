<template>
  <el-dialog
    v-model="dialogVisible"
    title="忘记密码"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-steps :active="currentStep" align-center class="steps">
      <el-step title="验证用户" />
      <el-step title="回答问题" />
      <el-step title="重置密码" />
    </el-steps>

    <!-- 步骤1: 输入用户名 -->
    <el-form
      v-if="currentStep === 0"
      :model="step1Form"
      :rules="step1Rules"
      ref="step1FormRef"
      class="form-container"
    >
      <el-form-item label="用户名" prop="username">
        <el-input
          v-model="step1Form.username"
          placeholder="请输入用户名"
          prefix-icon="User"
        />
      </el-form-item>
    </el-form>

    <!-- 步骤2: 回答安全问题 -->
    <el-form
      v-if="currentStep === 1"
      :model="step2Form"
      :rules="step2Rules"
      ref="step2FormRef"
      class="form-container"
    >
      <el-alert
        :title="securityQuestion"
        type="info"
        :closable="false"
        show-icon
        class="question-alert"
      />
      <el-form-item label="安全答案" prop="answer">
        <el-input
          v-model="step2Form.answer"
          placeholder="请输入安全答案"
          prefix-icon="Key"
        />
      </el-form-item>
    </el-form>

    <!-- 步骤3: 设置新密码 -->
    <el-form
      v-if="currentStep === 2"
      :model="step3Form"
      :rules="step3Rules"
      ref="step3FormRef"
      class="form-container"
    >
      <el-form-item label="新密码" prop="newPassword">
        <el-input
          v-model="step3Form.newPassword"
          type="password"
          placeholder="请输入新密码"
          prefix-icon="Lock"
          show-password
        />
      </el-form-item>
      <el-form-item label="确认密码" prop="confirmPassword">
        <el-input
          v-model="step3Form.confirmPassword"
          type="password"
          placeholder="请再次输入新密码"
          prefix-icon="Lock"
          show-password
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button v-if="currentStep > 0" @click="handlePrevious">上一步</el-button>
        <el-button type="primary" @click="handleNext" :loading="loading">
          {{ currentStep === 2 ? '完成' : '下一步' }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import axios from 'axios'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits(['update:modelValue', 'success'])

const dialogVisible = ref(props.modelValue)
const currentStep = ref(0)
const loading = ref(false)
const securityQuestion = ref('')

const step1FormRef = ref<FormInstance>()
const step2FormRef = ref<FormInstance>()
const step3FormRef = ref<FormInstance>()

const step1Form = reactive({
  username: ''
})

const step2Form = reactive({
  answer: ''
})

const step3Form = reactive({
  newPassword: '',
  confirmPassword: ''
})

const step1Rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ]
}

const step2Rules: FormRules = {
  answer: [
    { required: true, message: '请输入安全答案', trigger: 'blur' }
  ]
}

const step3Rules: FormRules = {
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== step3Form.newPassword) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const handleNext = async () => {
  if (currentStep.value === 0) {
    // 验证用户名并获取安全问题
    const valid = await step1FormRef.value?.validate()
    if (!valid) return

    loading.value = true
    try {
      const response = await axios.post('/api/auth/forgot-password', {
        username: step1Form.username
      })

      if (response.data.success) {
        securityQuestion.value = response.data.security_question
        currentStep.value = 1
        ElMessage.success('请回答安全问题')
      }
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '验证失败')
    } finally {
      loading.value = false
    }
  } else if (currentStep.value === 1) {
    // 验证安全答案
    const valid = await step2FormRef.value?.validate()
    if (!valid) return

    currentStep.value = 2
  } else if (currentStep.value === 2) {
    // 重置密码
    const valid = await step3FormRef.value?.validate()
    if (!valid) return

    loading.value = true
    try {
      const response = await axios.post('/api/auth/reset-password', {
        username: step1Form.username,
        security_answer: step2Form.answer,
        new_password: step3Form.newPassword,
        confirm_password: step3Form.confirmPassword
      })

      if (response.data.success) {
        ElMessage.success('密码重置成功，请使用新密码登录')
        emit('success')
        handleCancel()
      }
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '重置失败')
    } finally {
      loading.value = false
    }
  }
}

const handlePrevious = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const handleCancel = () => {
  dialogVisible.value = false
  emit('update:modelValue', false)
  
  // 重置表单
  currentStep.value = 0
  step1Form.username = ''
  step2Form.answer = ''
  step3Form.newPassword = ''
  step3Form.confirmPassword = ''
  securityQuestion.value = ''
}

// 监听 props 变化
import { watch } from 'vue'
watch(() => props.modelValue, (val) => {
  dialogVisible.value = val
})

watch(dialogVisible, (val) => {
  if (!val) {
    emit('update:modelValue', false)
  }
})
</script>

<style scoped>
.steps {
  margin-bottom: 30px;
}

.form-container {
  padding: 20px 0;
}

.question-alert {
  margin-bottom: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
