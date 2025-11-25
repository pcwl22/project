<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h2>超市空货架检测系统</h2>
        <p>基于 YOLOv8 的智能检测</p>
      </div>
      <el-tabs v-model="activeMode" class="login-tabs">
        <el-tab-pane label="登录" name="login"></el-tab-pane>
        <el-tab-pane label="注册" name="register"></el-tab-pane>
      </el-tabs>
      <el-form :model="loginForm" :rules="rules" ref="loginFormRef" class="login-form">
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            @keyup.enter="activeMode === 'login' ? handleLogin() : null"
          />
        </el-form-item>
        <el-form-item prop="confirmPassword" v-if="activeMode === 'register'">
          <el-input
            v-model="loginForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            prefix-icon="Lock"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="captcha" v-if="activeMode === 'register'">
          <div style="display: flex; gap: 10px; width: 100%;">
            <el-input
              v-model="loginForm.captcha"
              placeholder="请输入验证码"
              prefix-icon="Key"
              size="large"
              style="flex: 1;"
              @keyup.enter="handleRegister"
            />
            <div class="captcha-box" @click="refreshCaptcha">
              <span class="captcha-text">{{ captchaCode }}</span>
            </div>
          </div>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            @click="activeMode === 'login' ? handleLogin() : handleRegister()"
            :loading="loading"
            class="login-button"
            size="large"
          >
            {{ activeMode === 'login' ? '登录' : '注册' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer" v-if="activeMode === 'login'">
        <p>没有账号？<el-button type="primary" link @click="activeMode = 'register'">去注册</el-button></p>
      </div>
      <div class="login-footer" v-else>
        <p>已有账号？<el-button type="primary" link @click="activeMode = 'login'">去登录</el-button></p>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'

const emit = defineEmits(['login-success'])

const loginFormRef = ref<FormInstance>()
const loading = ref(false)
const activeMode = ref('login')

const loginForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  captcha: ''
})

// 验证码生成
const captchaCode = ref('')
const generateCaptcha = () => {
  const chars = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'
  let code = ''
  for (let i = 0; i < 4; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  captchaCode.value = code
}
const refreshCaptcha = () => {
  generateCaptcha()
  loginForm.captcha = ''
}

// 初始化验证码
generateCaptcha()

const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (activeMode.value === 'register') {
    if (value === '') {
      callback(new Error('请再次输入密码'))
    } else if (value !== loginForm.password) {
      callback(new Error('两次输入密码不一致'))
    } else {
      callback()
    }
  } else {
    callback()
  }
}

const validateCaptcha = (rule: any, value: any, callback: any) => {
  if (activeMode.value === 'register') {
    if (value === '') {
      callback(new Error('请输入验证码'))
    } else if (value.toLowerCase() !== captchaCode.value.toLowerCase()) {
      callback(new Error('验证码错误'))
    } else {
      callback()
    }
  } else {
    callback()
  }
}

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名长度不能小于3位', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 5, message: '密码长度不能小于5位', trigger: 'blur' }
  ],
  confirmPassword: [
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  captcha: [
    { validator: validateCaptcha, trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      
      try {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(loginForm)
        })
        
        if (response.ok) {
          const data = await response.json()
          ElMessage.success(data.message || '登录成功！')
          emit('login-success', data.user_id, data.is_admin)
        } else {
          const error = await response.json()
          ElMessage.error(error.detail || '用户名或密码错误！')
          // 密码错误后清空密码框
          loginForm.password = ''
        }
      } catch (error) {
        ElMessage.error('登录失败，请检查网络连接')
        console.error('Login error:', error)
      } finally {
        loading.value = false
      }
    }
  })
}

const handleRegister = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      
      try {
        const response = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(loginForm)
        })
        
        if (response.ok) {
          const data = await response.json()
          ElMessage.success(data.message || '注册成功！')
          // 注册成功后自动登录
          emit('login-success', data.user_id, data.is_admin)
        } else {
          const error = await response.json()
          ElMessage.error(error.detail || '注册失败！')
          // 失败后刷新验证码
          refreshCaptcha()
        }
      } catch (error) {
        ElMessage.error('注册失败，请检查网络连接')
        console.error('Register error:', error)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-box {
  width: 100%;
  max-width: 400px;
  background: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: fadeInScale 0.5s ease-out;
}

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-header p {
  margin: 8px 0 0;
  font-size: 14px;
  color: #909399;
}

.login-tabs {
  margin-top: 20px;
}

.login-tabs :deep(.el-tabs__item) {
  font-size: 16px;
}

.login-form {
  margin-top: 30px;
}

.login-button {
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.login-footer p {
  margin: 0;
  font-size: 12px;
  color: #909399;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.captcha-box {
  width: 120px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
  transition: all 0.3s ease;
}

.captcha-box:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.captcha-text {
  font-size: 20px;
  font-weight: bold;
  color: white;
  letter-spacing: 4px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}
</style>
