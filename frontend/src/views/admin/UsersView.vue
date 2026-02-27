<template>
  <div>
    <div class="page-header">
      <el-input v-model="keyword" placeholder="搜索用户名/联系方式"
                clearable prefix-icon="Search" style="width:260px" @keyup.enter="load" />
      <el-button type="primary" @click="load">搜索</el-button>
    </div>

    <el-table :data="users" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="contact" label="联系方式" />
      <el-table-column label="角色" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_admin ? 'danger' : 'info'" size="small">
            {{ row.is_admin ? '管理员' : '普通用户' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'warning'" size="small">
            {{ row.is_active ? '正常' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="注册时间" width="160">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openReset(row)">重置密码</el-button>
          <el-button size="small" :type="row.is_active ? 'warning' : 'success'"
                     @click="toggleActive(row)">
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
          <el-button size="small" :type="row.is_admin ? 'info' : 'danger'"
                     @click="toggleAdmin(row)">
            {{ row.is_admin ? '取消管理员' : '设为管理员' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="resetDialog" title="重置密码" width="360px">
      <el-form label-width="80px">
        <el-form-item label="新密码">
          <el-input v-model="newPassword" type="password" show-password placeholder="至少6位" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetDialog = false">取消</el-button>
        <el-button type="primary" :loading="opLoading" @click="doReset">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { apiAdminGetUsers, apiAdminUpdateUser } from '@/api'

const users = ref([])
const loading = ref(false)
const keyword = ref('')
const resetDialog = ref(false)
const newPassword = ref('')
const opLoading = ref(false)
const currentUser = ref(null)

function formatDate(t) { return new Date(t).toLocaleString('zh-CN') }

async function load() {
  loading.value = true
  try {
    const res = await apiAdminGetUsers({ keyword: keyword.value })
    users.value = res
  } finally {
    loading.value = false
  }
}

async function toggleActive(row) {
  await apiAdminUpdateUser(row.id, { is_active: !row.is_active })
  row.is_active = !row.is_active
  ElMessage.success(row.is_active ? '已启用' : '已禁用')
}

async function toggleAdmin(row) {
  await apiAdminUpdateUser(row.id, { is_admin: !row.is_admin })
  row.is_admin = !row.is_admin
  ElMessage.success('操作成功')
}

function openReset(row) {
  currentUser.value = row
  newPassword.value = ''
  resetDialog.value = true
}

async function doReset() {
  if (newPassword.value.length < 6) { ElMessage.warning('密码至少6位'); return }
  opLoading.value = true
  try {
    await apiAdminUpdateUser(currentUser.value.id, { new_password: newPassword.value })
    ElMessage.success('密码重置成功')
    resetDialog.value = false
  } finally {
    opLoading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page-header { display: flex; gap: 10px; margin-bottom: 16px; }
</style>
