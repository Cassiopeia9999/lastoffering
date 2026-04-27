<template>
  <div class="ai-insights-page" v-loading="loading">
    <section class="hero-grid">
      <el-card v-for="card in topKpis" :key="card.key" shadow="never" class="hero-card" :class="card.tone">
        <div class="hero-label">{{ card.label }}</div>
        <div class="hero-value">{{ card.value }}%</div>
        <div class="hero-meta">{{ card.meta }}</div>
      </el-card>
    </section>

    <el-row :gutter="20">
      <el-col :lg="14" :md="24">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-header">
              <span>核心效果指标</span>
              <span class="panel-note">用于评估智能匹配与闭环流程的实际效果</span>
            </div>
          </template>
          <v-chart class="chart chart-lg" :option="effectOption" autoresize />
        </el-card>
      </el-col>

      <el-col :lg="10" :md="24">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-header">
              <span>AI模块覆盖率</span>
              <span class="panel-note">各子模块当前的可用程度</span>
            </div>
          </template>
          <v-chart class="chart chart-lg" :option="moduleRadarOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :lg="12" :md="24">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-header">
              <span>字段质量评分</span>
              <span class="panel-note">多模态匹配依赖字段的完整度情况</span>
            </div>
          </template>
          <v-chart class="chart chart-md" :option="qualityOption" autoresize />
        </el-card>
      </el-col>

      <el-col :lg="12" :md="24">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-header">
              <span>指标说明</span>
              <span class="panel-note">答辩时可直接用于解释图表含义</span>
            </div>
          </template>

          <div class="note-list">
            <div v-for="item in explainList" :key="item.label" class="note-item">
              <div class="note-label">{{ item.label }}</div>
              <div class="note-text">{{ item.text }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, RadarChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  RadarComponent,
  TooltipComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

import { apiAdminGetAiStats } from '@/api'

use([
  CanvasRenderer,
  BarChart,
  RadarChart,
  GridComponent,
  LegendComponent,
  RadarComponent,
  TooltipComponent,
])

const loading = ref(false)
const aiStats = ref({})

const overview = computed(() => aiStats.value.overview || {})
const effects = computed(() => aiStats.value.effect_metrics || {})
const quality = computed(() => aiStats.value.data_quality || [])

function toneByValue(value, inverse = false) {
  if (!inverse) {
    if (value >= 70) return 'good'
    if (value >= 40) return 'medium'
    return 'risk'
  }
  if (value <= 30) return 'good'
  if (value <= 60) return 'medium'
  return 'risk'
}

const topKpis = computed(() => [
  {
    key: 'match_confirmation_rate',
    label: '匹配确认率',
    value: effects.value.match_confirmation_rate || 0,
    meta: `${overview.value.confirmed_matches || 0} / ${overview.value.total_matches || 0}`,
    tone: toneByValue(effects.value.match_confirmation_rate || 0),
  },
  {
    key: 'claim_completion_rate',
    label: '认领完成率',
    value: effects.value.claim_completion_rate || 0,
    meta: `${overview.value.completed_matches || 0} / ${overview.value.confirmed_matches || 0}`,
    tone: toneByValue(effects.value.claim_completion_rate || 0),
  },
  {
    key: 'ai_closed_loop_rate',
    label: 'AI闭环成功率',
    value: effects.value.ai_closed_loop_rate || 0,
    meta: `${overview.value.completed_matches || 0} / ${overview.value.total_matches || 0}`,
    tone: toneByValue(effects.value.ai_closed_loop_rate || 0),
  },
  {
    key: 'rejection_rate',
    label: '误匹配率',
    value: effects.value.rejection_rate || 0,
    meta: '数值越低越好',
    tone: toneByValue(effects.value.rejection_rate || 0, true),
  },
])

const effectOption = computed(() => ({
  color: ['#16a34a', '#2563eb', '#8b5cf6', '#ef4444'],
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 18, right: 18, top: 20, bottom: 18, containLabel: true },
  xAxis: {
    type: 'value',
    max: 100,
    splitLine: { lineStyle: { color: '#e2e8f0' } },
    axisLabel: { color: '#64748b', formatter: '{value}%' },
  },
  yAxis: {
    type: 'category',
    data: ['匹配确认率', '认领完成率', 'AI闭环成功率', '误匹配率'],
    axisTick: { show: false },
    axisLine: { show: false },
    axisLabel: { color: '#334155' },
  },
  series: [
    {
      type: 'bar',
      barWidth: 18,
      data: [
        effects.value.match_confirmation_rate || 0,
        effects.value.claim_completion_rate || 0,
        effects.value.ai_closed_loop_rate || 0,
        effects.value.rejection_rate || 0,
      ],
      itemStyle: {
        borderRadius: [0, 10, 10, 0],
      },
      label: {
        show: true,
        position: 'right',
        color: '#475569',
        formatter: '{c}%',
      },
    },
  ],
}))

const moduleRadarOption = computed(() => ({
  color: ['#2563eb'],
  tooltip: {},
  radar: {
    radius: '66%',
    splitNumber: 5,
    axisName: { color: '#334155' },
    splitArea: {
      areaStyle: {
        color: ['rgba(37,99,235,0.03)', 'rgba(37,99,235,0.06)'],
      },
    },
    splitLine: { lineStyle: { color: '#cbd5e1' } },
    axisLine: { lineStyle: { color: '#cbd5e1' } },
    indicator: [
      { name: '图像分类', max: 100 },
      { name: '典型特征', max: 100 },
      { name: '关键词提取', max: 100 },
      { name: '数据质量', max: 100 },
    ],
  },
  series: [
    {
      type: 'radar',
      symbol: 'circle',
      symbolSize: 8,
      areaStyle: { color: 'rgba(37, 99, 235, 0.18)' },
      lineStyle: { width: 2, color: '#2563eb' },
      data: [
        {
          value: [
            effects.value.classification_coverage_rate || 0,
            effects.value.feature_completion_rate || 0,
            effects.value.keyword_completion_rate || 0,
            overview.value.avg_quality || 0,
          ],
          name: 'AI模块评估',
        },
      ],
    },
  ],
}))

const qualityOption = computed(() => ({
  color: ['#0ea5e9'],
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 18, right: 18, top: 10, bottom: 10, containLabel: true },
  xAxis: {
    type: 'value',
    max: 100,
    splitLine: { lineStyle: { color: '#e2e8f0' } },
    axisLabel: { color: '#64748b', formatter: '{value}%' },
  },
  yAxis: {
    type: 'category',
    data: quality.value.map((item) => item.label),
    axisTick: { show: false },
    axisLine: { show: false },
    axisLabel: { color: '#334155' },
  },
  series: [
    {
      type: 'bar',
      barWidth: 14,
      data: quality.value.map((item) => item.coverage),
      itemStyle: {
        borderRadius: [0, 8, 8, 0],
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 1,
          y2: 0,
          colorStops: [
            { offset: 0, color: '#38bdf8' },
            { offset: 1, color: '#0f766e' },
          ],
        },
      },
      label: {
        show: true,
        position: 'right',
        color: '#475569',
        formatter: '{c}%',
      },
    },
  ],
}))

const explainList = computed(() => [
  {
    label: '匹配确认率',
    text: '表示系统给出的匹配结果中，有多少最终被人工确认有效，用于衡量推荐准确性。',
  },
  {
    label: '认领完成率',
    text: '表示进入确认阶段的匹配中，有多少最终真正完成线下交接，用于衡量闭环能力。',
  },
  {
    label: '误匹配率',
    text: '表示被人工判定为无效或被拒绝的匹配比例，这个指标越低越好。',
  },
  {
    label: '模块覆盖率',
    text: '表示图像分类、关键词提取、典型特征提取等模块对现有数据的有效处理比例。',
  },
])

onMounted(async () => {
  loading.value = true
  try {
    aiStats.value = await apiAdminGetAiStats()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.ai-insights-page {
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
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: #fff;
}

.hero-card.good {
  background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 100%);
}

.hero-card.medium {
  background: linear-gradient(180deg, #fff7ed 0%, #ffffff 100%);
}

.hero-card.risk {
  background: linear-gradient(180deg, #fef2f2 0%, #ffffff 100%);
}

.hero-label,
.panel-header span:first-child {
  font-weight: 700;
  color: #0f172a;
}

.hero-value {
  margin-top: 14px;
  font-size: 36px;
  font-weight: 800;
  color: #0f172a;
}

.hero-meta,
.panel-note,
.note-text {
  font-size: 12px;
  line-height: 1.6;
  color: #64748b;
}

.hero-meta {
  margin-top: 8px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
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

.note-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.note-item {
  padding: 16px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 18px;
  background: linear-gradient(135deg, #ffffff, #f8fbff);
}

.note-label {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.note-text {
  margin-top: 8px;
}

@media (max-width: 1200px) {
  .hero-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
