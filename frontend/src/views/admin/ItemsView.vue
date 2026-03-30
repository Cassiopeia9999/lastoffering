<template>
  <div>
    <div class="page-header">
      <el-input v-model="keyword" placeholder="搜索物品名称" clearable
                prefix-icon="Search" style="width:220px" />
      <el-select v-model="filterType" placeholder="类型" clearable style="width:110px">
        <el-option label="失物" value="lost" /><el-option label="招领" value="found" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width:120px">
        <el-option label="待认领" value="pending" />
        <el-option label="已匹配" value="matched" />
        <el-option label="已完成" value="closed" />
      </el-select>
      <el-select v-model="filterDeleted" placeholder="上架状态" clearable style="width:120px">
        <el-option label="正常" :value="false" /><el-option label="已下架" :value="true" />
      </el-select>
      <el-button type="primary" @click="load">搜索</el-button>
    </div>

    <el-table :data="items" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="类型" width="70">
        <template #default="{ row }">
          <el-tag :type="row.type === 'lost' ? 'danger' : 'success'" size="small">
            {{ row.type === 'lost' ? '失物' : '招领' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="140" />
      <el-table-column prop="category" label="类别" width="100" />
      <el-table-column prop="owner_username" label="发布者" width="100" />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag v-if="row.is_deleted" type="info" size="small">已下架</el-tag>
          <el-tag v-else :type="{ pending:'warning', matched:'primary', closed:'success' }[row.status]" size="small">
            {{ { pending:'待认领', matched:'已匹配', closed:'已完成' }[row.status] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="发布时间" width="130">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewItem(row.id)">查看</el-button>
          <!-- 修改状态下拉 -->
          <el-dropdown v-if="!row.is_deleted" size="small" @command="(s) => changeStatus(row, s)" style="margin: 0 4px">
            <el-button size="small" type="primary" plain>
              改状态<el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="pending" :disabled="row.status === 'pending'">待认领</el-dropdown-item>
                <el-dropdown-item command="matched" :disabled="row.status === 'matched'">已匹配</el-dropdown-item>
                <el-dropdown-item command="closed" :disabled="row.status === 'closed'">已完成</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <!-- 下架/恢复 -->
          <el-popconfirm v-if="!row.is_deleted" title="确认下架？" @confirm="deleteItem(row)">
            <template #reference>
              <el-button size="small" type="danger" plain>下架</el-button>
            </template>
          </el-popconfirm>
          <el-button v-else size="small" type="success" plain @click="restoreItem(row)">恢复</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-if="total > pageSize" background layout="prev,pager,next"
                   :total="total" :page-size="pageSize" v-model:current-page="page"
                   @current-change="load" style="margin-top:16px;display:flex;justify-content:center" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiAdminGetItems, apiAdminDeleteItem, apiAdminRestoreItem, apiAdminUpdateItemStatus } from '@/api'

const router = useRouter()
const items = ref([])
const loading = ref(false)
const keyword = ref('')
const filterType = ref('')
const filterStatus = ref('')
const filterDeleted = ref(undefined)
const page = ref(1)
const pageSize = 20
const total = ref(0)

function formatDate(t) {
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function load() {
  loading.value = true
  try {
    const res = await apiAdminGetItems({
      keyword: keyword.value || undefined,
      type: filterType.value || undefined,
      status: filterStatus.value || undefined,
      is_deleted: filterDeleted.value,
      page: page.value, page_size: pageSize,
    })
    items.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function viewItem(id) { router.push(`/items/${id}`) }

async function deleteItem(row) {
  await apiAdminDeleteItem(row.id)
  row.is_deleted = true
  ElMessage.success('已下架')
}

async function restoreItem(row) {
  await apiAdminRestoreItem(row.id)
  row.is_deleted = false
  ElMessage.success('已恢复')
}

async function changeStatus(row, status) {
  try {
    await apiAdminUpdateItemStatus(row.id, status)
    row.status = status
    const label = { pending: '待认领', matched: '已匹配', closed: '已完成' }[status]
    ElMessage.success(`状态已改为：${label}`)
  } catch (e) {
    ElMessage.error('状态修改失败')
  }
}

onMounted(load)
</script>

<style scoped>
.page-header { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
</style>
