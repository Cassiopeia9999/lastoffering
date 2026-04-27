<template>
  <div class="my-page">
    <section class="hero">
      <div>
        <p class="eyebrow">我的发布</p>
        <h1>管理你发布的寻物与招领信息</h1>
      </div>
      <el-button type="primary" class="publish-btn" @click="router.push('/publish')">
        <el-icon><Plus /></el-icon>
        发布新信息
      </el-button>
    </section>

    <el-tabs v-model="tab" class="my-tabs">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="寻物" name="lost" />
      <el-tab-pane label="招领" name="found" />
    </el-tabs>

    <div v-loading="loading">
      <el-empty v-if="!filteredItems.length" description="暂时没有发布记录" />

      <el-card
        v-for="item in filteredItems"
        :key="item.id"
        class="my-item-card"
        :class="{ 'is-closed': item.status === 'closed' }"
        shadow="never"
      >
        <div v-if="item.status === 'closed'" class="closed-ribbon">
          <el-icon><CircleCheck /></el-icon>
          已完成
        </div>

        <div class="my-item-inner">
          <div class="img-wrapper">
            <el-image v-if="item.image_url" :src="`/${item.image_url}`" fit="cover" class="my-item-img" />
            <div v-else class="my-item-img-placeholder"><el-icon><Picture /></el-icon></div>
          </div>

          <div class="my-item-info">
            <div class="my-item-top">
              <span class="pill" :class="item.type === 'lost' ? 'lost' : 'found'">
                {{ item.type === 'lost' ? '寻物' : '招领' }}
              </span>
              <span class="pill" :class="statusClass(item.status)">
                {{ statusText(item.status) }}
              </span>
              <span v-if="item.is_deleted" class="pill slate">已下架</span>
              <span v-if="item.category" class="pill violet">{{ item.category }}</span>
            </div>

            <div class="my-item-title" @click="router.push(`/items/${item.id}`)">{{ item.title }}</div>

            <div class="my-item-meta">
              <span v-if="item.location"><el-icon><Location /></el-icon> {{ item.location }}</span>
              <span><el-icon><Clock /></el-icon> {{ formatTime(item.created_at) }}</span>
            </div>
          </div>

          <div class="my-item-actions">
            <el-button @click="router.push(`/items/${item.id}`)">查看</el-button>
            <template v-if="!item.is_deleted && item.status !== 'closed'">
              <el-button type="primary" plain @click="router.push(`/publish?edit=${item.id}`)">编辑</el-button>
              <el-button type="warning" plain @click="offShelf(item)">下架</el-button>
              <el-popconfirm
                title="标记完成后无法重新上架，确认吗？"
                confirm-button-text="确认完成"
                cancel-button-text="取消"
                @confirm="markDone(item)"
              >
                <template #reference>
                  <el-button type="success" plain>标记完成</el-button>
                </template>
              </el-popconfirm>
            </template>
            <el-button v-if="item.is_deleted" type="success" @click="restore(item)">重新上架</el-button>
            <el-popconfirm
              title="确认删除该物品吗？删除后将仅在后台保留，前台不会再显示。"
              confirm-button-text="确认删除"
              cancel-button-text="取消"
              @confirm="deleteItem(item)"
            >
              <template #reference>
                <el-button type="danger" plain>删除</el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { CircleCheck, Clock, Location, Picture, Plus } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { apiCloseItem, apiDeleteItem, apiGetMyItems, apiOffShelfItem, apiRestoreItem } from '@/api'
import { getItemStatusMeta } from '@/utils/itemStatus'

const router = useRouter()
const items = ref([])
const loading = ref(false)
const tab = ref('all')

const filteredItems = computed(() => {
  const list = tab.value === 'all' ? items.value : items.value.filter((i) => i.type === tab.value)
  return [...list].sort((a, b) => {
    if (a.status === 'closed' && b.status !== 'closed') return 1
    if (a.status !== 'closed' && b.status === 'closed') return -1
    return 0
  })
})

function formatTime(t) {
  return new Date(t).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function statusText(status) {
  return getItemStatusMeta(status).label
}

function statusClass(status) {
  return getItemStatusMeta(status).className
}

async function deleteItem(item) {
  try {
    await apiDeleteItem(item.id)
    items.value = items.value.filter((i) => i.id !== item.id)
    ElMessage.success('已删除，该记录仅在后台保留')
  } catch {
    ElMessage.error('删除失败')
  }
}

async function offShelf(item) {
  try {
    await apiOffShelfItem(item.id)
    item.is_deleted = true
    ElMessage.success('已下架')
  } catch {
    ElMessage.error('下架失败')
  }
}

async function restore(item) {
  try {
    await apiRestoreItem(item.id)
    item.is_deleted = false
    ElMessage.success('已重新上架')
  } catch {
    ElMessage.error('重新上架失败')
  }
}

async function markDone(item) {
  try {
    await apiCloseItem(item.id)
    item.status = 'closed'
    ElMessage.success('已标记为完成')
  } catch {
    ElMessage.error('操作失败')
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await apiGetMyItems()
    items.value = res.items || []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.my-page {
  max-width: 1120px;
  margin: 0 auto;
}

.hero {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #2563eb;
}

.hero h1 {
  margin: 0;
  font-size: 30px;
  color: #0f172a;
}

.publish-btn {
  border-radius: 999px;
}

.my-tabs {
  margin-bottom: 12px;
}

.my-item-card {
  position: relative;
  overflow: hidden;
  margin-bottom: 14px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 20px;
  background: linear-gradient(135deg, #fff, #fbfdff);
}

.my-item-card.is-closed {
  opacity: 0.8;
}

.closed-ribbon {
  position: absolute;
  top: 14px;
  right: -28px;
  z-index: 1;
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 4px 36px;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
  transform: rotate(45deg);
  background: linear-gradient(135deg, #16a34a, #22c55e);
}

.my-item-inner {
  display: flex;
  gap: 18px;
  align-items: center;
}

.img-wrapper {
  flex-shrink: 0;
}

.my-item-img,
.my-item-img-placeholder {
  width: 94px;
  height: 94px;
  border-radius: 14px;
}

.my-item-img-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  background: linear-gradient(135deg, #f3f6fb, #eaf0f8);
}

.my-item-info {
  flex: 1;
  min-width: 0;
}

.my-item-top {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.pill {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.pill.lost {
  color: #b91c1c;
  background: #fee2e2;
}

.pill.found {
  color: #166534;
  background: #dcfce7;
}

.pill.pending {
  color: #b45309;
  background: #fef3c7;
}

.pill.matched {
  color: #1d4ed8;
  background: #dbeafe;
}

.pill.closed {
  color: #166534;
  background: #dcfce7;
}

.pill.slate {
  color: #475569;
  background: #e2e8f0;
}

.pill.violet {
  color: #7c3aed;
  background: #ede9fe;
}

.my-item-title {
  margin-bottom: 8px;
  color: #0f172a;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
}

.my-item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: #64748b;
}

.my-item-meta span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.my-item-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

:deep(.el-tabs__item) {
  font-size: 15px;
  font-weight: 600;
}

:deep(.el-tabs__item.is-active) {
  color: #2563eb;
}
</style>
