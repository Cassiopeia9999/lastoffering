<template>
  <el-card class="item-card" shadow="hover" @click="router.push(`/items/${item.id}`)">
    <div class="card-inner">
      <div class="img-wrapper">
        <el-image v-if="item.image_url" :src="`/${item.image_url}`" fit="cover" class="item-img" lazy>
          <template #error>
            <div class="img-placeholder"><el-icon size="32"><Picture /></el-icon></div>
          </template>
        </el-image>
        <div v-else class="img-placeholder"><el-icon size="32"><Picture /></el-icon></div>
        <div class="img-overlay">
          <el-icon size="20"><View /></el-icon>
        </div>
      </div>

      <div class="card-body">
        <div class="card-top">
          <span class="pill type-pill" :class="item.type === 'lost' ? 'lost' : 'found'">
            <el-icon v-if="item.type === 'lost'"><Warning /></el-icon>
            <el-icon v-else><Star /></el-icon>
            {{ item.type === 'lost' ? '失物' : '招领' }}
          </span>
          <span class="pill status-pill" :class="statusMeta.className">
            <el-icon v-if="statusIcon"><component :is="statusIcon" /></el-icon>
            {{ statusMeta.label }}
          </span>
          <span v-if="item.category" class="pill category-pill">{{ item.category }}</span>
        </div>

        <div class="card-title">{{ item.title }}</div>

        <div class="card-meta">
          <span v-if="item.location" class="meta-item">
            <el-icon><Location /></el-icon>
            {{ item.location }}
          </span>
          <span class="meta-item">
            <el-icon><Clock /></el-icon>
            {{ formatTime(item.created_at) }}
          </span>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { CircleCheck, Clock, Connection, Location, Picture, Star, View, Warning } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { getItemStatusMeta } from '@/utils/itemStatus'

const router = useRouter()
const props = defineProps({ item: { type: Object, required: true } })
const statusMeta = computed(() => getItemStatusMeta(props.item.status))

const statusIconMap = {
  Clock,
  Connection,
  CircleCheck,
}

const statusIcon = computed(() => statusIconMap[statusMeta.value.icon] || null)

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
.item-card {
  margin-bottom: 14px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid rgba(148, 163, 184, 0.16) !important;
  border-radius: 18px !important;
  transition: all 0.35s ease !important;
  background: linear-gradient(180deg, #fff, #fcfdff);
}

.item-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.1) !important;
  border-color: rgba(37, 99, 235, 0.24) !important;
}

.card-inner {
  display: flex;
  gap: 16px;
  padding: 6px;
}

.img-wrapper {
  position: relative;
  flex-shrink: 0;
  overflow: hidden;
  border-radius: 14px;
}

.item-img,
.img-placeholder {
  width: 102px;
  height: 102px;
  border-radius: 14px;
}

.item-img {
  object-fit: cover;
  transition: transform 0.35s ease;
}

.item-card:hover .item-img {
  transform: scale(1.06);
}

.img-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c9d6;
  background: linear-gradient(135deg, #f3f6fb, #eaf0f8);
}

.img-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.46);
  opacity: 0;
  transition: opacity 0.25s ease;
}

.img-overlay .el-icon {
  color: #fff;
}

.item-card:hover .img-overlay {
  opacity: 1;
}

.card-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  padding: 2px 0;
}

.card-top {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.type-pill.lost {
  color: #b91c1c;
  background: #fee2e2;
}

.type-pill.found {
  color: #166534;
  background: #dcfce7;
}

.status-pill.pending {
  color: #b45309;
  background: #fef3c7;
}

.status-pill.matched {
  color: #1d4ed8;
  background: #dbeafe;
}

.status-pill.closed {
  color: #166534;
  background: #dcfce7;
}

.category-pill {
  color: #7c3aed;
  background: #ede9fe;
}

.card-title {
  overflow: hidden;
  color: #0f172a;
  font-size: 16px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  color: #64748b;
  font-size: 13px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
</style>
