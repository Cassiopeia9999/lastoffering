<template>
  <div class="profile-wrap">
    <el-card shadow="never" class="profile-card">
      <!-- 头部：头像 + 基本信息 -->
      <div class="profile-header">
        <div class="avatar-block">
          <el-avatar :size="88" :src="avatarUrl" class="avatar-img">
            <span style="font-size:32px">{{ displayName.charAt(0).toUpperCase() }}</span>
          </el-avatar>
          <el-upload
            v-if="editing"
            :show-file-list="false"
            :before-upload="handleAvatarUpload"
            accept="image/*"
            class="avatar-uploader"
          >
            <el-button size="small" type="primary" plain round>
              <el-icon><Upload /></el-icon> 更换头像
            </el-button>
          </el-upload>
        </div>

        <div class="profile-meta">
          <div class="username-row">
            <span class="nickname">{{ info.nickname || info.username }}</span>
            <el-tag v-if="userStore.isAdmin" type="danger" size="small">管理员</el-tag>
            <el-tag v-else type="info" size="small">普通用户</el-tag>
          </div>
          <div class="account-name">账号：{{ info.username }}</div>
          <div class="signature">{{ info.signature || '这个人很懒，什么都没有留下~' }}</div>
          <div class="register-time">注册于 {{ formatDate(info.created_at) }}</div>
        </div>

        <div class="header-actions">
          <el-button v-if="!editing" type="primary" plain @click="startEdit">
            <el-icon><Edit /></el-icon> 编辑资料
          </el-button>
          <template v-else>
            <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
            <el-button @click="cancelEdit">取消</el-button>
          </template>
        </div>
      </div>

      <el-divider />

      <!-- 查看模式 -->
      <div v-if="!editing" class="info-grid">
        <div class="info-item" v-for="f in displayFields" :key="f.key">
          <span class="info-label">{{ f.label }}</span>
          <span class="info-value">{{ info[f.key] || '未填写' }}</span>
        </div>
      </div>

      <!-- 编辑模式 -->
      <el-form v-else ref="formRef" :model="form" label-width="88px" class="edit-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="昵称">
              <el-input v-model="form.nickname" placeholder="请输入昵称" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="真实姓名">
              <el-input v-model="form.real_name" placeholder="请输入真实姓名" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学院">
              <el-input v-model="form.college" placeholder="请输入所在学院" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="班级">
              <el-input v-model="form.class_name" placeholder="请输入班级" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系方式">
              <el-input v-model="form.contact" placeholder="手机号 / 微信 / 邮箱" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱">
              <el-input v-model="form.email" placeholder="请输入邮箱" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="个性签名">
              <el-input v-model="form.signature" placeholder="介绍一下自己吧~" maxlength="120" show-word-limit clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider>修改密码（不修改请留空）</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="新密码">
              <el-input v-model="form.password" type="password" placeholder="留空则不修改"
                        show-password clearable autocomplete="new-password" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="确认密码">
              <el-input v-model="confirmPassword" type="password" placeholder="再次输入新密码"
                        show-password clearable autocomplete="new-password" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit, Upload } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { apiUpdateMe, apiUploadAvatar } from '@/api'

const userStore = useUserStore()
const formRef = ref()
const editing = ref(false)
const saving = ref(false)
const confirmPassword = ref('')

// 从 store 读取用户信息
const info = computed(() => userStore.userInfo || {})
const displayName = computed(() => info.value.nickname || info.value.username || '')
const avatarUrl = computed(() => {
  if (!info.value.avatar) return ''
  // 如果是相对路径，拼接服务器地址
  if (info.value.avatar.startsWith('http')) return info.value.avatar
  return `http://localhost:8000/${info.value.avatar}`
})

const displayFields = [
  { key: 'username',  label: '账号' },
  { key: 'nickname',  label: '昵称' },
  { key: 'real_name', label: '真实姓名' },
  { key: 'college',   label: '学院' },
  { key: 'class_name',label: '班级' },
  { key: 'contact',   label: '联系方式' },
  { key: 'email',     label: '邮箱' },
]

// 编辑表单
const form = reactive({
  nickname: '', real_name: '', college: '', class_name: '',
  contact: '', email: '', signature: '', password: ''
})

function startEdit() {
  Object.assign(form, {
    nickname:   info.value.nickname   || '',
    real_name:  info.value.real_name  || '',
    college:    info.value.college    || '',
    class_name: info.value.class_name || '',
    contact:    info.value.contact    || '',
    email:      info.value.email      || '',
    signature:  info.value.signature  || '',
    password:   '',
  })
  confirmPassword.value = ''
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  confirmPassword.value = ''
}

async function handleSave() {
  if (form.password && form.password !== confirmPassword.value) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  saving.value = true
  try {
    const payload = {}
    const fields = ['nickname', 'real_name', 'college', 'class_name', 'contact', 'email', 'signature']
    fields.forEach(f => { if (form[f] !== '') payload[f] = form[f] })
    if (form.password) payload.password = form.password
    await apiUpdateMe(payload)
    await userStore.fetchMe()
    ElMessage.success('资料已更新')
    editing.value = false
    confirmPassword.value = ''
  } finally {
    saving.value = false
  }
}

async function handleAvatarUpload(file) {
  const fd = new FormData()
  fd.append('file', file)
  try {
    await apiUploadAvatar(fd)
    await userStore.fetchMe()
    ElMessage.success('头像更新成功')
  } catch {
    ElMessage.error('头像上传失败')
  }
  return false // 阻止 el-upload 自动上传
}

function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleDateString('zh-CN')
}

onMounted(() => userStore.fetchMe())
</script>

<style scoped>
.profile-wrap {
  padding: 12px 0 20px;
}
.profile-card {
  max-width: 920px;
  margin: 0 auto;
  border-radius: 24px;
  animation: fadeInUp 0.6s ease-out;
  background: linear-gradient(180deg, #ffffff, #fbfdff);
}

.profile-header {
  display: flex;
  align-items: flex-start;
  gap: 28px;
  padding: 14px;
  border-radius: 22px;
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.08), transparent 20%),
    linear-gradient(135deg, #f8fbff, #fffcf7);
}

.avatar-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}

.avatar-img {
  border: 4px solid #e2e8f0;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.12);
}

.profile-meta { flex: 1; }

.username-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.nickname {
  font-size: 28px;
  font-weight: 800;
  color: #0f172a;
}

.account-name {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 6px;
}

.signature {
  font-size: 14px;
  color: #334155;
  margin-bottom: 6px;
  line-height: 1.5;
}

.register-time {
  font-size: 13px;
  color: #94a3b8;
}

.header-actions { flex-shrink: 0; }

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px 40px;
  padding: 8px 6px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f8fbff 0%, #fffdf8 100%);
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 18px;
  transition: all 0.3s ease;
}

.info-item:hover {
  background: linear-gradient(135deg, #eef5ff 0%, #fffaf2 100%);
  transform: translateY(-2px);
}

.info-label {
  font-size: 13px;
  color: #909399;
}

.info-value {
  font-size: 15px;
  color: #303133;
  font-weight: 500;
}

.edit-form { margin-top: 8px; }

:deep(.el-divider__text) {
  font-weight: 600;
  color: #606266;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

:deep(.el-input__wrapper) {
  min-height: 42px;
  border-radius: 14px !important;
}

:deep(.el-avatar) {
  background: linear-gradient(135deg, #2563eb 0%, #0f172a 100%) !important;
}
</style>
