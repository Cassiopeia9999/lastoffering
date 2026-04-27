<template>
  <div class="admin-page">
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-grid">
        <el-input
          v-model="keyword"
          placeholder="搜索物品标题或描述"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select v-model="filterType" placeholder="类型" clearable @change="handleSearch">
          <el-option label="寻物" value="lost" />
          <el-option label="招领" value="found" />
        </el-select>

        <el-select v-model="filterState" placeholder="状态" clearable @change="handleSearch">
          <el-option label="进行中" value="in_progress" />
          <el-option label="待处理" value="pending" />
          <el-option label="已匹配" value="matched" />
          <el-option label="已完成" value="completed" />
          <el-option label="已下架" value="off_shelf" />
          <el-option label="已删除" value="deleted" />
        </el-select>

        <div class="toolbar-actions">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="table-card">
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="72" />

        <el-table-column label="类型" width="92">
          <template #default="{ row }">
            <span class="mini-pill" :class="row.type === 'lost' ? 'lost' : 'found'">
              {{ row.type === 'lost' ? '寻物' : '招领' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="title" label="标题" min-width="210" />
        <el-table-column prop="category" label="类别" width="130" />
        <el-table-column prop="owner_username" label="发布者" width="120" />

        <el-table-column label="状态" width="130">
          <template #default="{ row }">
            <span class="mini-pill" :class="displayStatusClass(row)">
              {{ displayStatusText(row) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="发布时间" width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>

        <el-table-column label="操作" width="360" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewItem(row.id)">查看</el-button>

            <el-dropdown
              v-if="canChangeWorkflow(row)"
              size="small"
              @command="(status) => changeStatus(row, status)"
            >
              <el-button size="small" plain type="primary">
                改状态
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="pending" :disabled="row.status === 'pending'">
                    待处理
                  </el-dropdown-item>
                  <el-dropdown-item command="matched" :disabled="row.status === 'matched'">
                    已匹配
                  </el-dropdown-item>
                  <el-dropdown-item command="closed" :disabled="row.status === 'closed'">
                    已完成
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>

            <el-button
              v-if="canOffShelf(row)"
              size="small"
              type="warning"
              plain
              @click="offShelfItem(row)"
            >
              下架
            </el-button>

            <el-button
              v-if="row.is_deleted || row.owner_deleted"
              size="small"
              type="success"
              plain
              @click="restoreItem(row)"
            >
              恢复
            </el-button>

            <el-button size="small" type="danger" plain @click="hardDeleteItem(row)">
              删除记录
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > pageSize"
        v-model:current-page="page"
        background
        layout="prev,pager,next"
        :total="total"
        :page-size="pageSize"
        class="pager"
        @current-change="load"
      />
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ArrowDown, Search } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  apiAdminDeleteItem,
  apiAdminGetItems,
  apiAdminHardDeleteItem,
  apiAdminRestoreItem,
  apiAdminUpdateItemStatus,
} from '@/api'

const router = useRouter()
const items = ref([])
const loading = ref(false)
const keyword = ref('')
const filterType = ref('')
const filterState = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getDisplayStatus(row) {
  if (row.owner_deleted) return 'deleted'
  if (row.is_deleted) return 'off_shelf'
  if (row.status === 'closed') return 'closed'
  if (row.status === 'matched') return 'matched'
  return 'pending'
}

function displayStatusText(row) {
  return {
    pending: '待处理',
    matched: '已匹配',
    closed: '已完成',
    off_shelf: '已下架',
    deleted: '已删除',
  }[getDisplayStatus(row)]
}

function displayStatusClass(row) {
  return {
    pending: 'amber',
    matched: 'blue',
    closed: 'green',
    off_shelf: 'slate',
    deleted: 'red',
  }[getDisplayStatus(row)]
}

function canChangeWorkflow(row) {
  return !row.is_deleted && !row.owner_deleted
}

function canOffShelf(row) {
  return !row.is_deleted && !row.owner_deleted
}

function buildQueryParams() {
  const params = {
    keyword: keyword.value || undefined,
    type: filterType.value || undefined,
    page: page.value,
    page_size: pageSize,
  }

  if (filterState.value === 'in_progress') {
    params.record_state = 'in_progress'
  } else if (filterState.value === 'completed') {
    params.record_state = 'completed'
  } else if (filterState.value === 'off_shelf') {
    params.record_state = 'off_shelf'
  } else if (filterState.value === 'deleted') {
    params.record_state = 'deleted'
  } else if (filterState.value === 'pending' || filterState.value === 'matched') {
    params.status = filterState.value
  }

  return params
}

async function load() {
  loading.value = true
  try {
    const res = await apiAdminGetItems(buildQueryParams())
    items.value = res.items || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  load()
}

function resetFilters() {
  keyword.value = ''
  filterType.value = ''
  filterState.value = ''
  page.value = 1
  load()
}

function viewItem(id) {
  router.push(`/items/${id}`)
}

async function offShelfItem(row) {
  try {
    await apiAdminDeleteItem(row.id)
    row.is_deleted = true
    row.owner_deleted = false
    ElMessage.success('已下架')
  } catch {
    ElMessage.error('下架失败')
  }
}

async function restoreItem(row) {
  try {
    await apiAdminRestoreItem(row.id)
    row.is_deleted = false
    row.owner_deleted = false
    ElMessage.success('已恢复')
  } catch {
    ElMessage.error('恢复失败')
  }
}

async function hardDeleteItem(row) {
  try {
    await ElMessageBox.confirm(
      `确定彻底删除“${row.title}”吗？该操作会同步清理关联留言与匹配记录。`,
      '删除记录',
      { type: 'warning' }
    )
    await apiAdminHardDeleteItem(row.id)
    items.value = items.value.filter((item) => item.id !== row.id)
    total.value = Math.max(0, total.value - 1)
    ElMessage.success('记录已删除')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function changeStatus(row, status) {
  try {
    await apiAdminUpdateItemStatus(row.id, status)
    row.status = status
    ElMessage.success(`状态已改为：${displayStatusText(row)}`)
  } catch {
    ElMessage.error('状态修改失败')
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
  grid-template-columns: minmax(0, 2fr) 140px 180px auto;
  gap: 12px;
  align-items: center;
}

.toolbar-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.mini-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.mini-pill.lost {
  color: #b91c1c;
  background: #fee2e2;
}

.mini-pill.found,
.mini-pill.green {
  color: #166534;
  background: #dcfce7;
}

.mini-pill.blue {
  color: #1d4ed8;
  background: #dbeafe;
}

.mini-pill.amber {
  color: #b45309;
  background: #fef3c7;
}

.mini-pill.slate {
  color: #475569;
  background: #e2e8f0;
}

.mini-pill.red {
  color: #b91c1c;
  background: #fee2e2;
}

.pager {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  min-height: 42px;
  border-radius: 14px !important;
  box-shadow: none !important;
}

@media (max-width: 1200px) {
  .toolbar-grid {
    grid-template-columns: 1fr 1fr;
  }

  .toolbar-actions {
    grid-column: 1 / -1;
    justify-content: stretch;
  }

  .toolbar-actions :deep(.el-button) {
    flex: 1;
  }
}
</style>
