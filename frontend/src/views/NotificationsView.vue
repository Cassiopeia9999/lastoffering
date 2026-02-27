<template>
  <div>
    <div class="page-header">
      <h2>我的通知</h2>
      <el-button v-if="notifications.length" @click="markAll" :loading="marking">
        全部标为已读
      </el-button>
    </div>

    <el-card shadow="never" v-loading="loading">
      <el-empty v-if="!notifications.length" description="暂无通知" />
      <div v-for="n in notifications" :key="n.id"
           class="notif-item" :class="{ unread: !n.is_read }"
           @click="handleClick(n)">
        <div class="notif-icon">
          <el-icon size="20" :color="iconColor(n.type)">
            <component :is="iconName(n.type)" />
          </el-icon>
        </div>
        <div class="notif-body">
          <div class="notif-content">{{ n.content }}</div>
          <div class="notif-time">{{ formatTime(n.created_at) }}</div>
        </div>
        <el-badge v-if="!n.is_read" is-dot class="unread-dot" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiGetNotifications, apiMarkRead, apiMarkAllRead } from '@/api'

const router = useRouter()
const notifications = ref([])
const loading = ref(false)
const marking = ref(false)

function iconName(type) {
  const map = { match_found: 'Bell', contact_shared: 'Phone', new_message: 'ChatDotRound', system: 'InfoFilled' }
  return map[type] || 'Bell'
}
function iconColor(type) {
  const map = { match_found: '#e6a23c', contact_shared: '#67c23a', new_message: '#409eff', system: '#909399' }
  return map[type] || '#409eff'
}
function formatTime(t) {
  return new Date(t).toLocaleString('zh-CN')
}

async function load() {
  loading.value = true
  try {
    const res = await apiGetNotifications()
    notifications.value = res.notifications
  } finally {
    loading.value = false
  }
}

async function handleClick(n) {
  if (!n.is_read) {
    await apiMarkRead(n.id)
    n.is_read = true
  }
  if (n.related_item_id) router.push(`/items/${n.related_item_id}`)
}

async function markAll() {
  marking.value = true
  try {
    await apiMarkAllRead()
    notifications.value.forEach(n => n.is_read = true)
  } finally {
    marking.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 18px; }
.notif-item {
  display: flex; align-items: flex-start; gap: 12px; padding: 14px 16px;
  border-bottom: 1px solid #f0f0f0; cursor: pointer; transition: background .15s;
  position: relative;
}
.notif-item:last-child { border-bottom: none; }
.notif-item:hover { background: #fafafa; }
.notif-item.unread { background: #fef9ec; }
.notif-icon {
  width: 36px; height: 36px; border-radius: 50%; background: #f5f7fa;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.notif-body { flex: 1; }
.notif-content { font-size: 14px; color: #303133; line-height: 1.6; white-space: pre-line; }
.notif-time { font-size: 12px; color: #c0c4cc; margin-top: 4px; }
.unread-dot { position: absolute; right: 16px; top: 50%; transform: translateY(-50%); }
</style>
