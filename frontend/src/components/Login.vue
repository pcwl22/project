<template>
  <div class="login-container">
    <div class="login-box glass-card">
      <div class="login-header">
        <div class="logo-icon">
          <el-icon><Monitor /></el-icon>
        </div>
        <h2>ShelfDetect</h2>
        <p>智能货架监测系统</p>
      </div>
      
      <el-tabs v-model="activeMode" class="login-tabs">
        <el-tab-pane label="登录" name="login"></el-tab-pane>
        <el-tab-pane label="注册" name="register"></el-tab-pane>
      </el-tabs>

      <el-form :model="loginForm" :rules="rules" ref="loginFormRef" class="login-form">
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
            class="custom-input"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            class="custom-input"
            @keyup.enter="activeMode === 'login' ? handleLogin() : null"
          />
        </el-form-item>
        <el-form-item prop="confirmPassword" v-if="activeMode === 'register'">
          <el-input
            v-model="loginForm.confirmPassword"
            type="password"
            placeholder="确认密码"
            prefix-icon="Lock"
            size="large"
            class="custom-input"
          />
        </el-form-item>
        <el-form-item prop="captcha" v-if="activeMode === 'register'">
          <div class="captcha-wrapper">
            <el-input
              v-model="loginForm.captcha"
              placeholder="验证码"
              prefix-icon="Key"
              size="large"
              class="custom-input"
              @keyup.enter="handleRegister"
            />
            <div class="captcha-box" @click="refreshCaptcha">
              <span class="captcha-text">{{ captchaCode }}</span>
            </div>
          </div>
        </el-form-item>
        
        <!-- 注册时的安全问题 -->
        <el-form-item v-if="activeMode === 'register'" prop="securityQuestion">
          <el-select
            v-model="loginForm.securityQuestion"
            placeholder="选择或输入安全问题（必填）"
            size="large"
            class="custom-input"
            allow-create
            filterable
            default-first-option
          >
            <el-option label="您的出生地是？" value="您的出生地是？" />
            <el-option label="您母亲的姓名是？" value="您母亲的姓名是？" />
            <el-option label="您的小学名称是？" value="您的小学名称是？" />
            <el-option label="您最喜欢的颜色是？" value="您最喜欢的颜色是？" />
            <el-option label="您的宠物名字是？" value="您的宠物名字是？" />
            <el-option label="您最喜欢的电影是？" value="您最喜欢的电影是？" />
            <el-option label="您父亲的生日是？" value="您父亲的生日是？" />
            <el-option label="您的学号是？" value="您的学号是？" />
          </el-select>
        </el-form-item>
        
        <el-form-item v-if="activeMode === 'register'" prop="securityAnswer">
          <el-input
            v-model="loginForm.securityAnswer"
            placeholder="安全答案（必填）"
            prefix-icon="Key"
            size="large"
            class="custom-input"
          />
        </el-form-item>
        
        <!-- 忘记密码链接 -->
        <div v-if="activeMode === 'login'" class="forgot-password-link">
          <el-link type="primary" @click="showForgotPassword = true">忘记密码？</el-link>
        </div>
        
        <el-form-item>
          <el-button
            type="primary"
            @click="activeMode === 'login' ? handleLogin() : handleRegister()"
            :loading="loading"
            class="login-button"
            size="large"
          >
            {{ activeMode === 'login' ? '登 录' : '注 册' }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
    
    <!-- 忘记密码对话框 -->
    <ForgotPassword v-model="showForgotPassword" @success="handleForgotPasswordSuccess" />
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { Monitor } from '@element-plus/icons-vue'
import ForgotPassword from './ForgotPassword.vue'

const emit = defineEmits(['login-success'])

const loginFormRef = ref<FormInstance>()
const loading = ref(false)
const activeMode = ref('login')
const showForgotPassword = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  captcha: '',
  securityQuestion: '',
  securityAnswer: ''
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
  ],
  securityQuestion: [
    { required: true, message: '请选择或输入安全问题', trigger: 'change' }
  ],
  securityAnswer: [
    { required: true, message: '请输入安全答案', trigger: 'blur' },
    { min: 2, message: '安全答案长度不能小于2位', trigger: 'blur' }
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
          body: JSON.stringify({
            username: loginForm.username,
            password: loginForm.password,
            confirmPassword: loginForm.confirmPassword,
            captcha: loginForm.captcha,
            security_question: loginForm.securityQuestion,
            security_answer: loginForm.securityAnswer
          })
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

const handleForgotPasswordSuccess = () => {
  ElMessage.success('密码已重置，请使用新密码登录')
  activeMode.value = 'login'
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.forgot-password-link {
  text-align: right;
  margin-bottom: 15px;
}

/* Background Decoration */
.login-container::before {
  content: '';
  position: absolute;
  top: -10%;
  left: -10%;
  width: 50%;
  height: 50%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  border-radius: 50%;
}

.login-container::after {
  content: '';
  position: absolute;
  bottom: -10%;
  right: -10%;
  width: 50%;
  height: 50%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  border-radius: 50%;
}

.login-box {
  width: 100%;
  max-width: 420px;
  padding: 40px;
  position: relative;
  z-index: 1;
  animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 32px;
  margin: 0 auto 20px;
  box-shadow: 0 10px 20px rgba(99, 102, 241, 0.3);
}

.login-header h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
  letter-spacing: -0.5px;
}

.login-header p {
  margin: 8px 0 0;
  font-size: 14px;
  color: #6b7280;
}

.login-tabs {
  margin-bottom: 30px;
}

.login-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: rgba(0,0,0,0.05);
}

.login-tabs :deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 500;
  color: #6b7280;
}

.login-tabs :deep(.el-tabs__item.is-active) {
  color: var(--primary-color);
  font-weight: 600;
}

.login-tabs :deep(.el-tabs__active-bar) {
  background-color: var(--primary-color);
  height: 3px;
  border-radius: 3px;
}

.custom-input :deep(.el-input__wrapper) {
  background: rgba(243, 244, 246, 0.6);
  box-shadow: none;
  border: 1px solid transparent;
  transition: all 0.3s ease;
}

.custom-input :deep(.el-input__wrapper:hover),
.custom-input :deep(.el-input__wrapper.is-focus) {
  background: white;
  box-shadow: 0 0 0 1px var(--primary-color);
}

.captcha-wrapper {
  display: flex;
  gap: 12px;
}

.captcha-box {
  width: 120px;
  height: 40px;
  background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.captcha-box:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.captcha-text {
  font-size: 20px;
  font-weight: bold;
  color: white;
  letter-spacing: 4px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 1px;
  background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
  border: none;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
}
</style>
