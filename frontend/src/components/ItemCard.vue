<template>
  <el-card class="item-card" shadow="hover" @click="router.push(`/items/${item.id}`)">
    <div class="card-inner">
      <el-image v-if="item.image_url" :src="`/${item.image_url}`"
                fit="cover" class="item-img" lazy>
        <template #error>
          <div class="img-placeholder"><el-icon size="32"><Picture /></el-icon></div>
        </template>
      </el-image>
      <div v-else class="img-placeholder"><el-icon size="32"><Picture /></el-icon></div>

      <div class="card-body">
        <div class="card-top">
          <el-tag :type="item.type === 'lost' ? 'danger' : 'success'" size="small">
            {{ item.type === 'lost' ? '失物' : '招领' }}
          </el-tag>
          <el-tag v-if="item.status === 'matched'" type="info" size="small">已匹配</el-tag>
          <el-tag v-if="item.category" size="small" effect="plain">{{ item.category }}</el-tag>
        </div>
        <div class="card-title">{{ item.title }}</div>
        <div class="card-meta">
          <span v-if="item.location"><el-icon><Location /></el-icon> {{ item.location }}</span>
          <span><el-icon><Clock /></el-icon> {{ formatTime(item.created_at) }}</span>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
defineProps({ item: { type: Object, required: true } })

function formatTime(t) {
  if (!t) return ''
  const d = new Date(t)
  const now = new Date()
  const diff = (now - d) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  return `${d.getMonth() + 1}月${d.getDate()}日`
}
</script>

<style scoped>
.item-card { margin-bottom: 12px; cursor: pointer; border-radius: 10px; transition: transform .2s; }
.item-card:hover { transform: translateY(-2px); }
.card-inner { display: flex; gap: 12px; }
.item-img { width: 90px; height: 90px; border-radius: 8px; flex-shrink: 0; object-fit: cover; }
.img-placeholder {
  width: 90px; height: 90px; border-radius: 8px; flex-shrink: 0;
  background: #f5f7fa; display: flex; align-items: center; justify-content: center;
  color: #c0c4cc;
}
.card-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 6px; }
.card-top { display: flex; gap: 6px; flex-wrap: wrap; }
.card-title { font-size: 15px; font-weight: 600; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-meta { display: flex; gap: 12px; color: #909399; font-size: 12px; }
.card-meta span { display: flex; align-items: center; gap: 3px; }
</style>
