<template>
  <div class="notifications-page">
    <section class="hero">
      <div>
        <p class="eyebrow">消息中心</p>
        <h1>查看系统通知、匹配提醒与留言动态</h1>
      </div>
      <el-button v-if="notifications.length" class="mark-btn" @click="markAll" :loading="marking">
        全部标为已读
      </el-button>
    </section>

    <el-card shadow="never" class="notif-card" v-loading="loading">
      <el-empty v-if="!notifications.length" description="暂时还没有通知" />

      <div
        v-for="n in notifications"
        :key="n.id"
        class="notif-item"
        :class="{ unread: !n.is_read }"
        @click="handleClick(n)"
      >
        <div class="notif-icon">
          <el-icon size="20" :color="iconColor(n.type)">
            <component :is="iconName(n.type)" />
          </el-icon>
        </div>
        <div class="notif-body">
          <div class="notif-row">
            <div class="notif-title">{{ notifTitle(n.type) }}</div>
            <div class="notif-time">{{ formatTime(n.created_at) }}</div>
          </div>
          <div class="notif-content">{{ n.content }}</div>
        </div>
        <span v-if="!n.is_read" class="unread-pill">未读</span>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, ChatDotRound, InfoFilled, Phone } from '@element-plus/icons-vue'

import { apiGetNotifications, apiMarkAllRead, apiMarkRead } from '@/api'

const router = useRouter()
const notifications = ref([])
const loading = ref(false)
const marking = ref(false)

function iconName(type) {
  const map = { match_found: Bell, contact_shared: Phone, new_message: ChatDotRound, system: InfoFilled }
  return map[type] || Bell
}

function iconColor(type) {
  const map = { match_found: '#f59e0b', contact_shared: '#16a34a', new_message: '#2563eb', system: '#64748b' }
  return map[type] || '#2563eb'
}

function notifTitle(type) {
  const map = {
    match_found: '智能匹配提醒',
    contact_shared: '联系方式通知',
    new_message: '新的留言回复',
    system: '系统消息',
  }
  return map[type] || '通知'
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
    notifications.value.forEach((n) => {
      n.is_read = true
    })
  } finally {
    marking.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.notifications-page {
  max-width: 1040px;
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

.mark-btn {
  border-radius: 999px;
}

.notif-card {
  border-radius: 24px;
}

.notif-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  position: relative;
  padding: 18px 20px;
  cursor: pointer;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
  transition: all 0.25s ease;
}

.notif-item:last-child {
  border-bottom: none;
}

.notif-item:hover {
  background: linear-gradient(135deg, #f8fbff, #fffdf8);
}

.notif-item.unread {
  background: linear-gradient(135deg, #fff8e8, #fffdf5);
}

.notif-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  flex-shrink: 0;
  border-radius: 14px;
  background: linear-gradient(135deg, #f3f6fb, #eaf0f8);
}

.notif-body {
  flex: 1;
}

.notif-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.notif-title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.notif-time {
  font-size: 12px;
  color: #94a3b8;
}

.notif-content {
  margin-top: 6px;
  font-size: 14px;
  line-height: 1.8;
  color: #475569;
  white-space: pre-line;
}

.unread-pill {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #b45309;
  background: #fef3c7;
}
</style>
