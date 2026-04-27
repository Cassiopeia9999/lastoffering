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
        <h2>注册账号</h2>
        <p>加入校园失物招领平台</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="4-20位字母或数字" size="large"
                    prefix-icon="User" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="至少6位"
                    size="large" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item label="联系方式" prop="contact">
          <el-input v-model="form.contact" placeholder="手机号 / 微信号 / 邮箱（用于认领联系）"
                    size="large" prefix-icon="Phone" clearable />
        </el-form-item>
        <el-alert type="info" :closable="false" show-icon class="privacy-hint">
          联系方式仅在双方确认匹配后互相可见，请放心填写真实信息。
        </el-alert>
        <el-button type="primary" size="large" :loading="loading"
                   class="register-btn" @click="handleRegister">
          注 册
        </el-button>
      </el-form>

      <div class="auth-footer">
        已有账号？<el-link type="primary" class="login-link" @click="router.push('/login')">立即登录</el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiRegister } from '@/api'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

const form = reactive({ username: '', password: '', contact: '' })
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  contact: [{ required: true, message: '请填写联系方式', trigger: 'blur' }],
}

async function handleRegister() {
  await formRef.value.validate()
  loading.value = true
  try {
    await apiRegister(form)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
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
  margin-bottom: 28px;
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
.privacy-hint {
  margin-bottom: 16px;
  border-radius: 10px;
}
.register-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  border-radius: 12px !important;
  transition: all 0.3s ease !important;
}
.register-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4) !important;
}
.auth-footer {
  text-align: center;
  margin-top: 24px;
  color: #909399;
  font-size: 14px;
}
.login-link {
  font-weight: 500;
  color: #667eea !important;
}
</style>
