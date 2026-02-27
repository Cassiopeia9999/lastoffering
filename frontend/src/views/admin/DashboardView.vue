<template>
  <div v-loading="loading">
    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-bottom:24px">
      <el-col :span="6" v-for="card in statCards" :key="card.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-inner">
            <div class="stat-icon" :style="{ background: card.bg }">
              <el-icon size="22" color="#fff"><component :is="card.icon" /></el-icon>
            </div>
            <div>
              <div class="stat-num">{{ card.value }}</div>
              <div class="stat-label">{{ card.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <!-- 类别分布 -->
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span style="font-weight:600">物品类别分布</span></template>
          <div v-if="categoryStats.length">
            <div v-for="c in categoryStats" :key="c.category" class="cat-row">
              <span class="cat-name">{{ c.category }}</span>
              <el-progress :percentage="catPercent(c.count)" :stroke-width="10"
                           style="flex:1;margin:0 12px" />
              <span class="cat-count">{{ c.count }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>

      <!-- 近7天发布趋势 -->
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span style="font-weight:600">近30天发布趋势</span></template>
          <div v-if="dailyStats.length" class="daily-list">
            <div v-for="d in dailyStats.slice(-7)" :key="d.date+d.type" class="daily-row">
              <span class="daily-date">{{ d.date.slice(5) }}</span>
              <el-tag :type="d.type === 'lost' ? 'danger' : 'success'" size="small">
                {{ d.type === 'lost' ? '失物' : '招领' }}
              </el-tag>
              <el-progress :percentage="+(d.count / maxDaily * 100).toFixed(0)"
                           :stroke-width="8" style="flex:1;margin:0 10px" />
              <span>{{ d.count }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiAdminGetStats, apiAdminGetCategoryStats, apiAdminGetDailyStats } from '@/api'

const loading = ref(false)
const stats = ref({})
const categoryStats = ref([])
const dailyStats = ref([])

const maxDaily = computed(() => Math.max(...dailyStats.value.map(d => d.count), 1))
const maxCat = computed(() => Math.max(...categoryStats.value.map(c => c.count), 1))
const catPercent = (n) => +(n / maxCat.value * 100).toFixed(0)

const statCards = computed(() => [
  { label: '注册用户', value: stats.value.total_users || 0, icon: 'User', bg: '#409eff' },
  { label: '物品总数', value: stats.value.total_items || 0, icon: 'List', bg: '#e6a23c' },
  { label: '成功认领', value: stats.value.confirmed_matches || 0, icon: 'CircleCheck', bg: '#67c23a' },
  { label: '未读通知', value: stats.value.unread_notifications || 0, icon: 'Bell', bg: '#f56c6c' },
])

onMounted(async () => {
  loading.value = true
  try {
    const [s, c, d] = await Promise.all([
      apiAdminGetStats(), apiAdminGetCategoryStats(), apiAdminGetDailyStats()
    ])
    stats.value = s
    categoryStats.value = c.categories
    dailyStats.value = d.daily
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.stat-card { border-radius: 10px; }
.stat-inner { display: flex; align-items: center; gap: 16px; }
.stat-icon { width: 48px; height: 48px; border-radius: 10px; display: flex; align-items: center; justify-content: center; }
.stat-num { font-size: 26px; font-weight: 700; color: #303133; }
.stat-label { font-size: 13px; color: #909399; }
.cat-row { display: flex; align-items: center; margin-bottom: 10px; }
.cat-name { width: 80px; font-size: 13px; color: #606266; flex-shrink: 0; }
.cat-count { width: 30px; text-align: right; font-size: 13px; color: #909399; }
.daily-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 13px; }
.daily-date { width: 40px; color: #909399; flex-shrink: 0; }
</style>
