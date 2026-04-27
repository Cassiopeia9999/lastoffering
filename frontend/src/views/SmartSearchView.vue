<template>
  <div class="smart-search-page">
    <section class="hero">
      <div>
        <p class="eyebrow">智能寻物</p>
        <h1>把你记得的线索直接说出来</h1>
        <p class="hero-text">
          系统会先进行本地快速筛选，再尝试用 AI 做语义增强。你可以直接描述物品、颜色、品牌、地点和典型特征。
        </p>
      </div>
    </section>

    <el-row :gutter="24">
      <el-col :lg="9" :md="10" :sm="24">
        <el-card shadow="never" class="search-panel">
          <div class="panel-title">自然语言检索</div>

          <div class="example-box">
            <div class="example-label">输入示例</div>
            <div class="example-text">{{ activeExample }}</div>
            <div class="example-actions">
              <el-button text @click="prevExample">上一条</el-button>
              <el-button text @click="nextExample">下一条</el-button>
            </div>
          </div>

          <el-input
            v-model="message"
            type="textarea"
            :rows="7"
            resize="none"
            maxlength="300"
            show-word-limit
            placeholder="例如：我在教学楼丢了一个黑色小米充电宝，外壳有划痕。"
          />

          <div class="actions">
            <el-button @click="fillDemo">填入示例</el-button>
            <el-button type="primary" :loading="loading" @click="handleSearch">开始检索</el-button>
          </div>

          <transition name="fade-slide">
            <div v-if="stageVisible" class="stage-box">
              <div class="stage-head">
                <span class="stage-dot" :class="searchStage" />
                <strong>{{ stageTitle }}</strong>
              </div>
              <p class="stage-text">{{ stageText }}</p>
              <div class="runtime-strip">
                <div class="runtime-card runtime-card-local" :class="{ active: searchStage === 'fast' }">
                  <div class="runtime-label">本地快速</div>
                  <div class="runtime-value">{{ localDisplayTime }}</div>
                </div>
                <div class="runtime-card runtime-card-ai" :class="{ active: searchStage === 'full' }">
                  <div class="runtime-label">AI 增强</div>
                  <div class="runtime-value">{{ aiDisplayTime }}</div>
                </div>
              </div>
            </div>
          </transition>

          <div v-if="versionOptions.length" class="version-box">
            <div class="version-title">结果版本</div>
            <el-radio-group v-model="selectedVersion" size="large">
              <el-radio-button
                v-for="option in versionOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </el-radio-button>
            </el-radio-group>
            <div class="version-tip">{{ selectedVersionTip }}</div>
          </div>

          <div v-if="displayReply" class="reply-box">{{ displayReply }}</div>

          <div v-if="filterTags.length" class="filter-tags">
            <el-tag v-for="tag in filterTags" :key="tag" effect="dark" round>{{ tag }}</el-tag>
          </div>
        </el-card>
      </el-col>

      <el-col :lg="15" :md="14" :sm="24">
        <el-card shadow="never" class="result-panel">
          <template #header>
            <div class="result-header">
              <span>匹配结果</span>
              <div class="result-header-right">
                <span v-if="displayResults.length" class="result-count">{{ displayResults.length }} 条</span>
                <span v-if="selectedVersionBadge" class="selected-badge" :class="selectedVersion">
                  {{ selectedVersionBadge }}
                </span>
              </div>
            </div>
          </template>

          <div v-if="!searched" class="placeholder-state">
            <el-icon size="60"><ChatDotRound /></el-icon>
            <p>输入自然语言后，系统会先快速筛选，再用 AI 进一步理解语义并给出更贴近的结果。</p>
          </div>

          <template v-else>
            <div v-if="searchStage !== 'idle'" class="progress-banner">
              <div class="progress-main">{{ stageTitle }}</div>
              <div class="progress-sub">{{ stageText }}</div>
            </div>

            <el-empty
              v-if="!displayResults.length && searchStage === 'idle'"
              description="当前没有找到高相关结果，可以补充更多线索后再试。"
              :image-size="72"
            />

            <div v-else-if="displayResults.length" class="result-list">
              <div
                v-for="record in displayResults"
                :key="`${record.item.id}-${selectedVersion}`"
                class="result-card"
              >
                <ItemCard :item="record.item" />
                <div class="result-extra">
                  <div class="score-row">
                    <span>匹配度</span>
                    <strong>{{ Math.round(record.score * 100) }}%</strong>
                  </div>
                  <div class="reason-row">{{ record.reasons?.join('、') || '系统已根据综合特征完成排序' }}</div>
                </div>
              </div>
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound } from '@element-plus/icons-vue'

import ItemCard from '@/components/ItemCard.vue'
import { apiAssistantSearch } from '@/api'

const examples = [
  '我今天上午在图书馆丢了一个黑色小米充电宝，外壳有点划痕。',
  '我在教室1407丢了一个青色的红米耳机，应该是下课时落下的。',
  '我昨天可能在二田或者篮球场附近丢了一个黑色书包。',
  '我可能在竹园或者天猫超市附近丢了校园卡。',
  '我在第一田径场丢了一把钥匙，上面挂着蓝色挂件。',
  '我在梅园食堂附近掉了一个白色充电器，像小米120W那种。',
]

const loading = ref(false)
const searched = ref(false)
const message = ref('')
const searchStage = ref('idle')
const activeExampleIndex = ref(0)
const localResult = ref(null)
const aiResult = ref(null)
const selectedVersion = ref('local')
const fastElapsedMs = ref(null)
const fullElapsedMs = ref(null)
const liveElapsedMs = ref(0)

let stageTimer = null
let stageStartedAt = 0

const activeExample = computed(() => examples[activeExampleIndex.value])
const stageVisible = computed(() => searchStage.value !== 'idle' || fastElapsedMs.value !== null || fullElapsedMs.value !== null)

const stageTitle = computed(() => {
  if (searchStage.value === 'fast') return '本地模型正在快速提取线索'
  if (searchStage.value === 'full') return 'AI 正在进行语义增强检索'
  if (fullElapsedMs.value !== null) return 'AI 增强检索已完成'
  if (fastElapsedMs.value !== null) return '本地快速检索已完成'
  return ''
})

const stageText = computed(() => {
  if (searchStage.value === 'fast') return '系统会先基于本地规则、同义词归一化和关键词召回做首轮筛选。'
  if (searchStage.value === 'full') return '系统正在结合大模型理解你的描述，并生成更贴近语义的匹配结果。'
  if (fullElapsedMs.value !== null) return '你可以在本地快速版和 AI 增强版之间切换查看结果差异。'
  if (fastElapsedMs.value !== null) return '本地结果已就绪，系统正在继续生成 AI 增强结果。'
  return ''
})

const versionOptions = computed(() => {
  const options = []
  if (localResult.value) options.push({ value: 'local', label: '本地快速版' })
  if (aiResult.value) options.push({ value: 'ai', label: 'AI 增强版' })
  return options
})

const currentResult = computed(() => {
  if (selectedVersion.value === 'ai' && aiResult.value) return aiResult.value
  if (localResult.value) return localResult.value
  return aiResult.value
})

const displayReply = computed(() => currentResult.value?.reply || '')
const displayFilters = computed(() => currentResult.value?.filters || {})
const displayResults = computed(() => currentResult.value?.items || [])

const selectedVersionBadge = computed(() => {
  if (selectedVersion.value === 'ai' && aiResult.value) return '当前显示：AI 增强版'
  if (selectedVersion.value === 'local' && localResult.value) return '当前显示：本地快速版'
  return ''
})

const selectedVersionTip = computed(() => {
  if (selectedVersion.value === 'ai' && aiResult.value) {
    return `AI 增强版会结合语义理解、地点归一化和特征抽取，耗时 ${formatElapsed(fullElapsedMs.value)}`
  }
  if (localResult.value) {
    return `本地快速版依赖规则解析、关键词召回和语义归一化，耗时 ${formatElapsed(fastElapsedMs.value)}`
  }
  return ''
})

const filterTags = computed(() => {
  const tags = []
  const filters = displayFilters.value
  if (!filters || !Object.keys(filters).length) return tags

  if (selectedVersion.value === 'ai' && aiResult.value) tags.push('AI增强解析')
  if (selectedVersion.value === 'local' && localResult.value) tags.push('本地快速解析')
  if (filters.intent === 'lost') tags.push('查询招领信息')
  if (filters.intent === 'found') tags.push('查询寻物信息')
  if (filters.category) tags.push(`类别：${filters.category}`)
  if (filters.color) tags.push(`颜色：${filters.color}`)
  if (filters.brand) tags.push(`品牌：${filters.brand}`)
  if (filters.raw_location) tags.push(`原始地点：${filters.raw_location}`)
  if (filters.normalized_location) tags.push(`归一地点：${filters.normalized_location}`)
  if (filters.feature_text) tags.push(`典型特征：${filters.feature_text}`)
  return tags
})

const localDisplayTime = computed(() => {
  if (searchStage.value === 'fast') return formatElapsed(liveElapsedMs.value)
  return fastElapsedMs.value !== null ? formatElapsed(fastElapsedMs.value) : '--'
})

const aiDisplayTime = computed(() => {
  if (searchStage.value === 'full') return formatElapsed(liveElapsedMs.value)
  return fullElapsedMs.value !== null ? formatElapsed(fullElapsedMs.value) : '--'
})

function formatElapsed(ms) {
  if (ms === null || ms === undefined) return '--'
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function startStageTimer() {
  stopStageTimer()
  stageStartedAt = performance.now()
  liveElapsedMs.value = 0
  stageTimer = window.setInterval(() => {
    liveElapsedMs.value = performance.now() - stageStartedAt
  }, 100)
}

function stopStageTimer() {
  if (stageTimer) {
    window.clearInterval(stageTimer)
    stageTimer = null
  }
}

function prevExample() {
  activeExampleIndex.value = (activeExampleIndex.value - 1 + examples.length) % examples.length
}

function nextExample() {
  activeExampleIndex.value = (activeExampleIndex.value + 1) % examples.length
}

function fillDemo() {
  message.value = activeExample.value
}

watch(versionOptions, (options) => {
  if (!options.some((item) => item.value === selectedVersion.value) && options.length) {
    selectedVersion.value = options[options.length - 1].value
  }
})

async function handleSearch() {
  const trimmed = message.value.trim()
  if (!trimmed) {
    ElMessage.warning('请输入要检索的物品线索')
    return
  }

  loading.value = true
  searched.value = true
  searchStage.value = 'idle'
  localResult.value = null
  aiResult.value = null
  selectedVersion.value = 'local'
  fastElapsedMs.value = null
  fullElapsedMs.value = null
  liveElapsedMs.value = 0

  try {
    searchStage.value = 'fast'
    startStageTimer()
    const fastStarted = performance.now()
    const fastRes = await apiAssistantSearch({ message: trimmed, limit: 6, fast_only: true })
    fastElapsedMs.value = performance.now() - fastStarted
    localResult.value = fastRes
    selectedVersion.value = 'local'
    stopStageTimer()

    searchStage.value = 'full'
    startStageTimer()
    const fullStarted = performance.now()
    const fullRes = await apiAssistantSearch({ message: trimmed, limit: 6 })
    fullElapsedMs.value = performance.now() - fullStarted
    aiResult.value = fullRes
    selectedVersion.value = 'ai'
    stopStageTimer()
  } catch (error) {
    console.error('[SmartSearch] request failed', error)
    ElMessage.error(error?.response?.data?.detail || error?.message || '智能寻物请求失败')
  } finally {
    stopStageTimer()
    searchStage.value = 'idle'
    loading.value = false
  }
}

onBeforeUnmount(() => {
  stopStageTimer()
})
</script>

<style scoped>
.smart-search-page {
  max-width: 1240px;
  margin: 0 auto;
  animation: fadeInUp 0.5s ease-out;
}

.hero {
  margin-bottom: 22px;
  padding: 30px 32px;
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(250, 204, 21, 0.22), transparent 22%),
    linear-gradient(140deg, #fff9eb 0%, #ffffff 42%, #edf6ff 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 700;
  color: #d97706;
  letter-spacing: 0.08em;
}

.hero h1 {
  margin: 0;
  font-size: 34px;
  color: #0f172a;
}

.hero-text {
  margin: 10px 0 0;
  max-width: 760px;
  line-height: 1.8;
  color: #475569;
}

.search-panel,
.result-panel {
  border-radius: 24px;
}

.panel-title {
  margin-bottom: 14px;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.example-box {
  margin-bottom: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, #fff7d6, #f3f8ff);
}

.example-label {
  font-size: 12px;
  font-weight: 700;
  color: #b45309;
}

.example-text {
  margin-top: 6px;
  min-height: 52px;
  line-height: 1.7;
  color: #475569;
}

.example-actions {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}


.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 14px;
}

.stage-box {
  margin-top: 14px;
  padding: 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, #eff6ff, #fff7ed);
  border: 1px solid rgba(59, 130, 246, 0.12);
}

.stage-head {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #0f172a;
}

.stage-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #94a3b8;
  box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.35);
  animation: pulse 1.6s infinite;
}

.stage-dot.fast {
  background: #f59e0b;
}

.stage-dot.full {
  background: #2563eb;
}

.stage-text {
  margin: 8px 0 0;
  line-height: 1.7;
  color: #475569;
}

.runtime-strip {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.runtime-card {
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.72);
}

.runtime-card.active {
  transform: translateY(-1px);
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
}

.runtime-card-local.active {
  border-color: rgba(245, 158, 11, 0.32);
  background: linear-gradient(135deg, #fff7d6, #ffffff);
}

.runtime-card-ai.active {
  border-color: rgba(37, 99, 235, 0.28);
  background: linear-gradient(135deg, #eaf3ff, #ffffff);
}

.runtime-label {
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
}

.runtime-value {
  margin-top: 6px;
  font-size: 22px;
  font-weight: 800;
  color: #0f172a;
}

.version-box {
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  background: #0f172a;
  color: #f8fafc;
}

.version-title {
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.version-tip {
  margin-top: 10px;
  font-size: 12px;
  line-height: 1.7;
  color: rgba(248, 250, 252, 0.82);
}

.reply-box {
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 16px;
  background: #f8fafc;
  line-height: 1.8;
  color: #334155;
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 700;
}

.result-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.result-count {
  color: #2563eb;
}

.selected-badge {
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
}

.selected-badge.local {
  background: linear-gradient(135deg, #f59e0b, #ea580c);
}

.selected-badge.ai {
  background: linear-gradient(135deg, #2563eb, #0f172a);
}

.placeholder-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 380px;
  color: #94a3b8;
  text-align: center;
}

.progress-banner {
  margin-bottom: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(249, 115, 22, 0.08));
  border: 1px solid rgba(37, 99, 235, 0.08);
}

.progress-main {
  font-weight: 700;
  color: #0f172a;
}

.progress-sub {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.7;
  color: #64748b;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.result-card {
  padding: 10px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 20px;
  background: #fff;
}

.result-extra {
  padding: 6px 10px 2px;
}

.score-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #475569;
}

.score-row strong {
  color: #ea580c;
}

.reason-row {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.7;
  color: #64748b;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.35);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(59, 130, 246, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
  }
}
</style>










