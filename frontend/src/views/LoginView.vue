<template>
  <div class="auth-bg">
    <div class="auth-bg-pattern"></div>
    <div class="floating-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
      <div class="shape shape-4"></div>
    </div>
    <el-card class="auth-card" shadow="always">
      <div class="auth-logo">
        <div class="logo-icon-wrapper">
          <el-icon size="40"><Search /></el-icon>
        </div>
        <h2>校园失物招领</h2>
        <p>智能管理系统</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleLogin">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" size="large"
                    prefix-icon="User" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码"
                    size="large" prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-button type="primary" size="large" :loading="loading"
                   class="login-btn" @click="handleLogin">
          登 录
        </el-button>
      </el-form>

      <div class="auth-footer">
        还没有账号？<el-link type="primary" class="register-link" @click="router.push('/register')">立即注册</el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    await userStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push('/')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-bg {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}
.auth-bg-pattern {
  position: absolute;
  inset: 0;
  background-image: 
    radial-gradient(circle at 20% 80%, rgba(255,255,255,0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255,255,255,0.15) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(255,255,255,0.05) 0%, transparent 30%);
  pointer-events: none;
}
.floating-shapes {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
}
.shape-1 {
  width: 300px;
  height: 300px;
  background: #fff;
  top: -100px;
  left: -100px;
  animation: float 8s ease-in-out infinite;
}
.shape-2 {
  width: 200px;
  height: 200px;
  background: #fff;
  bottom: -50px;
  right: -50px;
  animation: float 6s ease-in-out infinite reverse;
}
.shape-3 {
  width: 150px;
  height: 150px;
  background: #fff;
  top: 50%;
  right: 10%;
  animation: float 7s ease-in-out infinite;
}
.shape-4 {
  width: 100px;
  height: 100px;
  background: #fff;
  bottom: 20%;
  left: 15%;
  animation: float 5s ease-in-out infinite reverse;
}
@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(10deg); }
}

.auth-card {
  width: 440px;
  border-radius: 24px !important;
  padding: 20px;
  backdrop-filter: blur(20px);
  background: rgba(255,255,255,0.95) !important;
  animation: fadeInUp 0.6s ease-out;
}
.auth-logo {
  text-align: center;
  margin-bottom: 32px;
}
.logo-icon-wrapper {
  width: 80px;
  height: 80px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}
.auth-logo h2 {
  margin: 0 0 6px;
  font-size: 24px;
  color: #303133;
  font-weight: 700;
}
.auth-logo p {
  color: #909399;
  font-size: 14px;
  margin: 0;
}
.login-btn {
  width: 100%;
  margin-top: 12px;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  border-radius: 12px !important;
  transition: all 0.3s ease !important;
}
.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4) !important;
}
.auth-footer {
  text-align: center;
  margin-top: 24px;
  color: #909399;
  font-size: 14px;
}
.register-link {
  font-weight: 500;
  color: #667eea !important;
}
</style>
