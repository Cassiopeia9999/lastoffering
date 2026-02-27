<template>
  <div class="profile-wrap">
    <el-card shadow="never" style="max-width:500px;margin:0 auto">
      <template #header><span style="font-weight:600">个人中心</span></template>

      <div class="avatar-row">
        <el-avatar :size="72" style="background:#409eff;font-size:28px">
          {{ userStore.username.charAt(0).toUpperCase() }}
        </el-avatar>
        <div>
          <div style="font-size:18px;font-weight:600">{{ userStore.username }}</div>
          <el-tag v-if="userStore.isAdmin" type="danger" size="small">管理员</el-tag>
          <el-tag v-else type="info" size="small">普通用户</el-tag>
        </div>
      </div>

      <el-divider />

      <el-form ref="formRef" :model="form" label-width="90px">
        <el-form-item label="联系方式">
          <el-input v-model="form.contact" placeholder="手机号 / 微信 / 邮箱" clearable />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="form.password" type="password" placeholder="不修改请留空"
                    show-password clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSave">保存修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { apiUpdateMe } from '@/api'

const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const form = reactive({ contact: '', password: '' })

onMounted(() => {
  form.contact = userStore.userInfo?.contact || ''
})

async function handleSave() {
  loading.value = true
  try {
    const payload = {}
    if (form.contact) payload.contact = form.contact
    if (form.password) payload.password = form.password
    await apiUpdateMe(payload)
    await userStore.fetchMe()
    ElMessage.success('修改成功')
    form.password = ''
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.profile-wrap { padding: 20px 0; }
.avatar-row { display: flex; align-items: center; gap: 16px; margin-bottom: 8px; }
</style>
