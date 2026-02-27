<template>
  <div class="auth-bg">
    <el-card class="auth-card" shadow="always">
      <div class="auth-logo">
        <el-icon size="40" color="#409eff"><Search /></el-icon>
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
        <el-alert type="info" :closable="false" show-icon style="margin-bottom:16px">
          联系方式仅在双方确认匹配后互相可见，请放心填写真实信息。
        </el-alert>
        <el-button type="primary" size="large" :loading="loading"
                   style="width:100%" @click="handleRegister">
          注 册
        </el-button>
      </el-form>

      <div class="auth-footer">
        已有账号？<el-link type="primary" @click="router.push('/login')">立即登录</el-link>
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
  background: linear-gradient(135deg, #1a6fc4 0%, #2d8cf0 60%, #74b9ff 100%);
  display: flex; align-items: center; justify-content: center;
}
.auth-card { width: 440px; border-radius: 16px; padding: 16px; }
.auth-logo { text-align: center; margin-bottom: 28px; }
.auth-logo h2 { margin: 12px 0 4px; font-size: 22px; color: #303133; }
.auth-logo p { color: #909399; font-size: 14px; margin: 0; }
.auth-footer { text-align: center; margin-top: 20px; color: #909399; font-size: 14px; }
</style>
