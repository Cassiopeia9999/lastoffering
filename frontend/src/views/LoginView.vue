<template>
  <div class="auth-bg">
    <el-card class="auth-card" shadow="always">
      <div class="auth-logo">
        <el-icon size="40" color="#409eff"><Search /></el-icon>
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
                   style="width:100%;margin-top:8px" @click="handleLogin">
          登 录
        </el-button>
      </el-form>

      <div class="auth-footer">
        还没有账号？<el-link type="primary" @click="router.push('/register')">立即注册</el-link>
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
  background: linear-gradient(135deg, #1a6fc4 0%, #2d8cf0 60%, #74b9ff 100%);
  display: flex; align-items: center; justify-content: center;
}
.auth-card { width: 420px; border-radius: 16px; padding: 16px; }
.auth-logo { text-align: center; margin-bottom: 28px; }
.auth-logo h2 { margin: 12px 0 4px; font-size: 22px; color: #303133; }
.auth-logo p { color: #909399; font-size: 14px; margin: 0; }
.auth-footer { text-align: center; margin-top: 20px; color: #909399; font-size: 14px; }
</style>
