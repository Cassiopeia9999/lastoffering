<template>
  <div>
    <div class="page-header">
      <h2>我的发布</h2>
      <el-button type="primary" @click="router.push('/publish')">
        <el-icon><Plus /></el-icon> 发布新信息
      </el-button>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="失物" name="lost" />
      <el-tab-pane label="招领" name="found" />
    </el-tabs>

    <div v-loading="loading">
      <el-empty v-if="!filteredItems.length" description="暂无发布记录" />
      <el-card v-for="item in filteredItems" :key="item.id" class="my-item-card" shadow="hover">
        <div class="my-item-inner">
          <el-image v-if="item.image_url" :src="`/${item.image_url}`"
                    fit="cover" class="my-item-img" />
          <div v-else class="my-item-img-placeholder"><el-icon><Picture /></el-icon></div>

          <div class="my-item-info">
            <div class="my-item-top">
              <el-tag :type="item.type === 'lost' ? 'danger' : 'success'" size="small">
                {{ item.type === 'lost' ? '失物' : '招领' }}
              </el-tag>
              <el-tag size="small" :type="statusType(item.status)">{{ statusLabel(item.status) }}</el-tag>
              <el-tag v-if="item.is_deleted" size="small" type="info">已下架</el-tag>
              <el-tag v-if="item.category" size="small" effect="plain">{{ item.category }}</el-tag>
            </div>
            <div class="my-item-title" @click="router.push(`/items/${item.id}`)">{{ item.title }}</div>
            <div class="my-item-meta">
              <span v-if="item.location"><el-icon><Location /></el-icon> {{ item.location }}</span>
              <span><el-icon><Clock /></el-icon> {{ formatTime(item.created_at) }}</span>
            </div>
          </div>

          <div class="my-item-actions">
            <el-button size="small" @click="router.push(`/items/${item.id}`)">查看</el-button>
            <template v-if="!item.is_deleted && item.status !== 'closed'">
              <el-button size="small" @click="router.push(`/publish?edit=${item.id}`)">编辑</el-button>
              <el-button size="small" type="warning" plain @click="offShelf(item)">下架</el-button>
              <el-popconfirm
                title="标记完成后无法重新上架，确认吗？"
                confirm-button-text="确认完成"
                cancel-button-text="取消"
                @confirm="markDone(item)">
                <template #reference>
                  <el-button size="small" type="success" plain>标记完成</el-button>
                </template>
              </el-popconfirm>
            </template>
            <el-button v-if="item.is_deleted" size="small" type="success" @click="restore(item)">重新上架</el-button>
            <el-popconfirm title="确认删除此物品？删除后无法恢复" @confirm="deleteItem(item)">
              <template #reference>
                <el-button size="small" type="danger" plain>删除</el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiGetMyItems, apiDeleteItem, apiRestoreItem, apiCloseItem } from '@/api'

const router = useRouter()
const items = ref([])
const loading = ref(false)
const tab = ref('all')

const filteredItems = computed(() =>
  tab.value === 'all' ? items.value : items.value.filter(i => i.type === tab.value)
)

function statusLabel(s) { return { pending: '待认领', matched: '已匹配', closed: '已完成' }[s] || s }
function statusType(s) { return { pending: 'warning', matched: 'info', closed: 'success' }[s] || '' }
function formatTime(t) {
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function deleteItem(item) {
  await apiDeleteItem(item.id)
  items.value = items.value.filter(i => i.id !== item.id)
  ElMessage.success('已删除')
}

async function offShelf(item) {
  await apiDeleteItem(item.id)
  item.is_deleted = true
  ElMessage.success('已下架')
}

async function restore(item) {
  try {
    await apiRestoreItem(item.id)
    item.is_deleted = false
    ElMessage.success('已重新上架')
  } catch (e) {
    ElMessage.error('重新上架失败')
  }
}

async function markDone(item) {
  try {
    await apiCloseItem(item.id)
    item.status = 'closed'
    ElMessage.success('已标记为完成')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await apiGetMyItems()
    items.value = res.items
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 18px; }
.my-item-card { margin-bottom: 12px; border-radius: 10px; }
.my-item-inner { display: flex; align-items: center; gap: 14px; }
.my-item-img { width: 80px; height: 80px; border-radius: 8px; object-fit: cover; flex-shrink: 0; }
.my-item-img-placeholder {
  width: 80px; height: 80px; border-radius: 8px; background: #f5f7fa;
  display: flex; align-items: center; justify-content: center; color: #c0c4cc; flex-shrink: 0;
}
.my-item-info { flex: 1; min-width: 0; }
.my-item-top { display: flex; gap: 6px; margin-bottom: 6px; flex-wrap: wrap; }
.my-item-title { font-size: 15px; font-weight: 600; color: #303133; cursor: pointer; margin-bottom: 4px; }
.my-item-title:hover { color: #409eff; }
.my-item-meta { display: flex; gap: 12px; color: #909399; font-size: 12px; }
.my-item-meta span { display: flex; align-items: center; gap: 3px; }
.my-item-actions { display: flex; gap: 6px; flex-shrink: 0; }
</style>
