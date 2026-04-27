<template>
  <div class="dashboard-page" v-loading="loading">
    <section class="hero-grid">
      <el-card v-for="card in statCards" :key="card.label" shadow="never" class="hero-card">
        <div class="hero-top">
          <span class="hero-label">{{ card.label }}</span>
          <span class="hero-badge" :style="{ background: card.badgeBg, color: card.badgeColor }">
            {{ card.badge }}
          </span>
        </div>
        <div class="hero-value">{{ card.value }}</div>
        <div class="hero-meta">{{ card.meta }}</div>
      </el-card>
    </section>

    <el-row :gutter="20">
      <el-col :lg="15" :md="24">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-header">
              <span>近 7 日发布趋势</span>
              <span class="panel-note">观察寻物与招领信息的近期活跃变化</span>
            </div>
          </template>
          <v-chart class="chart chart-lg" :option="trendOption" autoresize />
        </el-card>
      </el-col>

      <el-col :lg="9" :md="24">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-header">
              <span>流程状态分布</span>
              <span class="panel-note">展示当前在架记录的处理阶段结构</span>
            </div>
          </template>
          <v-chart class="chart chart-md" :option="workflowOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :lg="12" :md="24">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-header">
              <span>物品类别分布</span>
              <span class="panel-note">Top 8 类别的占比情况</span>
            </div>
          </template>
          <v-chart class="chart chart-md" :option="categoryOption" autoresize />
        </el-card>
      </el-col>

      <el-col :lg="12" :md="24">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-header">
              <span>数据规模概览</span>
              <span class="panel-note">与 AI 处理相关的样本与特征规模</span>
            </div>
          </template>
          <v-chart class="chart chart-md" :option="dataScaleOption" autoresize />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  TitleComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

import {
  apiAdminGetAiStats,
  apiAdminGetCategoryStats,
  apiAdminGetDailyStats,
  apiAdminGetStats,
} from '@/api'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  TitleComponent,
])

const loading = ref(false)
const stats = ref({})
const aiStats = ref({})
const categoryStats = ref([])
const dailyStats = ref([])

const aiOverview = computed(() => aiStats.value.overview || {})

const statCards = computed(() => [
  {
    label: '注册用户',
    value: stats.value.total_users || 0,
    meta: `当前活跃用户 ${stats.value.active_users || 0} 人`,
    badge: '用户侧',
    badgeBg: '#dbeafe',
    badgeColor: '#1d4ed8',
  },
  {
    label: '在架物品',
    value: stats.value.total_items || 0,
    meta: `寻物 ${stats.value.lost_items || 0} / 招领 ${stats.value.found_items || 0}`,
    badge: '业务侧',
    badgeBg: '#ffedd5',
    badgeColor: '#c2410c',
  },
  {
    label: '匹配申请',
    value: aiOverview.value.total_matches || 0,
    meta: `已确认 ${aiOverview.value.confirmed_matches || 0} / 已完成 ${aiOverview.value.completed_matches || 0}`,
    badge: '闭环侧',
    badgeBg: '#dcfce7',
    badgeColor: '#15803d',
  },
  {
    label: 'AI数据质量',
    value: `${aiOverview.value.avg_quality || 0}%`,
    meta: `关键词 ${aiOverview.value.keyword_items || 0} / 特征 ${aiOverview.value.feature_items || 0}`,
    badge: '数据侧',
    badgeBg: '#f3e8ff',
    badgeColor: '#7e22ce',
  },
])

const recentDailySeries = computed(() => {
  const rows = dailyStats.value || []
  const lastDates = [...new Set(rows.map((item) => item.date))].slice(-7)
  return lastDates.map((date) => {
    const lost = rows
      .filter((item) => item.date === date && item.type === 'lost')
      .reduce((sum, item) => sum + item.count, 0)
    const found = rows
      .filter((item) => item.date === date && item.type === 'found')
      .reduce((sum, item) => sum + item.count, 0)
    return { date: date.slice(5), lost, found }
  })
})

const trendOption = computed(() => ({
  color: ['#2563eb', '#16a34a'],
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0, icon: 'roundRect' },
  grid: { left: 18, right: 18, top: 20, bottom: 50, containLabel: true },
  xAxis: {
    type: 'category',
    data: recentDailySeries.value.map((item) => item.date),
    axisLine: { lineStyle: { color: '#cbd5e1' } },
    axisLabel: { color: '#64748b' },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#e2e8f0' } },
    axisLabel: { color: '#64748b' },
  },
  series: [
    {
      name: '寻物',
      type: 'line',
      smooth: true,
      symbolSize: 8,
      areaStyle: { color: 'rgba(37, 99, 235, 0.12)' },
      data: recentDailySeries.value.map((item) => item.lost),
    },
    {
      name: '招领',
      type: 'line',
      smooth: true,
      symbolSize: 8,
      areaStyle: { color: 'rgba(22, 163, 74, 0.12)' },
      data: recentDailySeries.value.map((item) => item.found),
    },
  ],
}))

const workflowOption = computed(() => ({
  color: ['#f59e0b', '#2563eb', '#16a34a'],
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, icon: 'circle' },
  series: [
    {
      type: 'pie',
      radius: ['48%', '74%'],
      center: ['50%', '44%'],
      label: { formatter: '{b}\n{d}%', color: '#334155', fontSize: 12 },
      data: [
        { name: '待处理', value: stats.value.pending_items || 0 },
        { name: '已匹配', value: stats.value.matched_items || 0 },
        { name: '已完成', value: aiOverview.value.completed_matches || 0 },
      ],
    },
  ],
}))

const categoryOption = computed(() => {
  const rows = (categoryStats.value || []).slice(0, 8)
  return {
    color: ['#0ea5e9'],
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 18, right: 18, top: 10, bottom: 10, containLabel: true },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b' },
    },
    yAxis: {
      type: 'category',
      data: rows.map((item) => item.category),
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: { color: '#334155' },
    },
    series: [
      {
        type: 'bar',
        data: rows.map((item) => item.count),
        barWidth: 16,
        itemStyle: {
          borderRadius: [0, 10, 10, 0],
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 1,
            y2: 0,
            colorStops: [
              { offset: 0, color: '#38bdf8' },
              { offset: 1, color: '#2563eb' },
            ],
          },
        },
      },
    ],
  }
})

const dataScaleOption = computed(() => ({
  color: ['#f97316', '#8b5cf6'],
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  legend: { bottom: 0, icon: 'roundRect' },
  grid: { left: 18, right: 18, top: 20, bottom: 42, containLabel: true },
  xAxis: {
    type: 'category',
    data: ['图片物品', '特征向量', '已分类', '关键词', '典型特征'],
    axisLine: { lineStyle: { color: '#cbd5e1' } },
    axisLabel: { color: '#64748b' },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#e2e8f0' } },
    axisLabel: { color: '#64748b' },
  },
  series: [
    {
      name: '样本量',
      type: 'bar',
      barWidth: 18,
      data: [
        aiOverview.value.image_items || 0,
        aiOverview.value.vector_items || 0,
        aiOverview.value.categorized_items || 0,
        aiOverview.value.keyword_items || 0,
        aiOverview.value.feature_items || 0,
      ],
      itemStyle: { borderRadius: [10, 10, 0, 0] },
    },
  ],
}))

onMounted(async () => {
  loading.value = true
  try {
    const [s, ai, c, d] = await Promise.all([
      apiAdminGetStats(),
      apiAdminGetAiStats(),
      apiAdminGetCategoryStats(),
      apiAdminGetDailyStats(),
    ])
    stats.value = s
    aiStats.value = ai
    categoryStats.value = c.categories || []
    dailyStats.value = d.daily || []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hero-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.hero-card,
.panel-card {
  border-radius: 24px;
}

.hero-card {
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.08), transparent 36%),
    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.hero-top,
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.hero-label,
.panel-header span:first-child {
  font-weight: 700;
  color: #0f172a;
}

.hero-badge {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.hero-value {
  margin-top: 18px;
  font-size: 36px;
  font-weight: 800;
  color: #0f172a;
}

.hero-meta,
.panel-note {
  font-size: 12px;
  line-height: 1.6;
  color: #64748b;
}

.hero-meta {
  margin-top: 8px;
}

.panel-note {
  font-weight: 500;
}

.chart {
  width: 100%;
}

.chart-lg {
  height: 340px;
}

.chart-md {
  height: 320px;
}

@media (max-width: 1200px) {
  .hero-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
