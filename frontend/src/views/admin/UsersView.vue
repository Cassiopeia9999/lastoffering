<template>
  <div class="admin-page">
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-grid">
        <el-input v-model="keyword" placeholder="搜索用户名或联系方式" clearable @keyup.enter="load">
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <div class="toolbar-actions">
          <el-button type="primary" @click="load">搜索</el-button>
          <el-button @click="keyword = ''; load()">重置</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="table-card">
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" min-width="140" />
        <el-table-column prop="contact" label="联系方式" min-width="160" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <span class="mini-pill" :class="roleClass(row)">
              {{ roleText(row) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <span class="mini-pill" :class="row.is_active ? 'green' : 'amber'">
              {{ row.is_active ? '正常' : '已禁用' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="420" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :disabled="!canManageAccount(row)" @click="openReset(row)">重置密码</el-button>
            <el-button
              size="small"
              :type="row.is_active ? 'warning' : 'success'"
              :disabled="!canManageAccount(row)"
              @click="toggleActive(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button
              size="small"
              :type="row.is_admin ? 'info' : 'danger'"
              :disabled="!canChangeRole(row)"
              @click="toggleAdmin(row)"
            >
              {{ row.is_admin ? '取消管理员' : '设为管理员' }}
            </el-button>
            <el-button
              v-if="row.is_superadmin"
              size="small"
              type="danger"
              plain
              :disabled="!canChangeRole(row)"
              @click="demoteSuperadmin(row)"
            >
              取消最高权限
            </el-button>
            <el-button
              v-else
              size="small"
              type="danger"
              plain
              :disabled="!canChangeRole(row)"
              @click="promoteSuperadmin(row)"
            >
              设为最高权限
            </el-button>
            <el-button size="small" type="danger" plain :disabled="!canManageAccount(row)" @click="openDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

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

    <el-dialog v-model="deleteDialog" title="确认删除用户" width="400px">
      <div class="delete-confirm">
        <el-icon size="48" color="#f56c6c"><WarningFilled /></el-icon>
        <p>确定要删除用户 <strong>{{ currentUser?.username }}</strong> 吗？</p>
        <p class="warn-text">该操作不可恢复，请谨慎执行。</p>
      </div>
      <template #footer>
        <el-button @click="deleteDialog = false">取消</el-button>
        <el-button type="danger" :loading="opLoading" @click="doDelete">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Search, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import { apiAdminDeleteUser, apiAdminGetUsers, apiAdminUpdateUser } from '@/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const users = ref([])
const loading = ref(false)
const keyword = ref('')
const resetDialog = ref(false)
const deleteDialog = ref(false)
const newPassword = ref('')
const opLoading = ref(false)
const currentUser = ref(null)

const currentId = computed(() => userStore.userInfo?.id)
const isSuperadmin = computed(() => userStore.isSuperadmin)

function formatDate(t) {
  return new Date(t).toLocaleString('zh-CN')
}

function roleText(row) {
  if (row.is_superadmin) return '超级管理员'
  if (row.is_admin) return '管理员'
  return '普通用户'
}

function roleClass(row) {
  if (row.is_superadmin) return 'danger'
  if (row.is_admin) return 'blue'
  return 'slate'
}

function canManageAccount(row) {
  if (row.id === currentId.value) return false
  if (row.is_superadmin && !isSuperadmin.value) return false
  if (row.is_admin && !isSuperadmin.value) return false
  return true
}

function canChangeRole(row) {
  if (!isSuperadmin.value) return false
  if (row.id === currentId.value) return false
  return true
}

async function load() {
  loading.value = true
  try {
    users.value = await apiAdminGetUsers({ keyword: keyword.value })
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
  await apiAdminUpdateUser(row.id, {
    is_admin: !row.is_admin,
    is_superadmin: false,
  })
  row.is_admin = !row.is_admin
  row.is_superadmin = false
  ElMessage.success('权限已更新')
}

async function promoteSuperadmin(row) {
  await apiAdminUpdateUser(row.id, {
    is_superadmin: true,
    is_admin: true,
  })
  row.is_superadmin = true
  row.is_admin = true
  ElMessage.success('已设为超级管理员')
}

async function demoteSuperadmin(row) {
  await apiAdminUpdateUser(row.id, {
    is_superadmin: false,
    is_admin: true,
  })
  row.is_superadmin = false
  row.is_admin = true
  ElMessage.success('已取消最高权限')
}

function openReset(row) {
  currentUser.value = row
  newPassword.value = ''
  resetDialog.value = true
}

async function doReset() {
  if (newPassword.value.length < 6) {
    ElMessage.warning('密码至少6位')
    return
  }
  opLoading.value = true
  try {
    await apiAdminUpdateUser(currentUser.value.id, { new_password: newPassword.value })
    ElMessage.success('密码重置成功')
    resetDialog.value = false
  } finally {
    opLoading.value = false
  }
}

function openDelete(row) {
  currentUser.value = row
  deleteDialog.value = true
}

async function doDelete() {
  opLoading.value = true
  try {
    await apiAdminDeleteUser(currentUser.value.id)
    users.value = users.value.filter((u) => u.id !== currentUser.value.id)
    deleteDialog.value = false
    ElMessage.success(`用户 ${currentUser.value.username} 已删除`)
  } finally {
    opLoading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.toolbar-card,
.table-card {
  border-radius: 22px;
}

.toolbar-grid {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
}

.toolbar-actions {
  display: flex;
  gap: 10px;
}

.mini-pill {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.mini-pill.green {
  color: #166534;
  background: #dcfce7;
}

.mini-pill.amber {
  color: #b45309;
  background: #fef3c7;
}

.mini-pill.danger {
  color: #b91c1c;
  background: #fee2e2;
}

.mini-pill.blue {
  color: #1d4ed8;
  background: #dbeafe;
}

.mini-pill.slate {
  color: #475569;
  background: #e2e8f0;
}

.delete-confirm {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  text-align: center;
}

.warn-text {
  color: #f56c6c;
  font-size: 13px;
}

:deep(.el-input__wrapper) {
  min-height: 42px;
  border-radius: 14px !important;
  box-shadow: none !important;
}
</style>
