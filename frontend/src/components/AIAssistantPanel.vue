<template>
  <div class="assistant-shell">
    <transition name="assistant-fade">
      <div v-if="visible" class="assistant-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title">AI 寻物助手</div>
            <div class="panel-subtitle">直接描述场景，我来帮你筛物品</div>
          </div>
          <el-button circle text @click="visible = false">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>

        <div class="panel-body">
          <div class="prompt-box">
            <div class="prompt-label">你可以这样说</div>
            <div class="prompt-example">“我今天上午在图书馆丢了一个黑色充电宝，外壳有划痕”</div>
          </div>

          <el-input
            v-model="message"
            type="textarea"
            :rows="4"
            resize="none"
            maxlength="300"
            show-word-limit
            placeholder="输入你丢失或捡到物品的自然语言描述"
          />

          <div class="panel-actions">
            <el-button :disabled="loading" @click="fillDemo">填入示例</el-button>
            <el-button type="primary" :loading="loading" @click="handleSearch">
              开始检索
            </el-button>
          </div>

          <div v-if="reply" class="assistant-reply">
            {{ reply }}
          </div>

          <div v-if="filtersSummary.length" class="filter-tags">
            <el-tag v-for="filter in filtersSummary" :key="filter" effect="plain">
              {{ filter }}
            </el-tag>
          </div>

          <div v-if="results.length" class="result-list">
            <div v-for="record in results" :key="record.item.id" class="result-card">
              <ItemCard :item="record.item" />
              <div class="result-extra">
                <div class="score-line">
                  <span>匹配分</span>
                  <b>{{ Math.round(record.score * 100) }}%</b>
                </div>
                <div class="reason-line">
                  {{ record.reasons?.join('；') || '多条件综合匹配' }}
                </div>
              </div>
            </div>
          </div>

          <el-empty
            v-else-if="searched && !loading"
            description="暂时没有找到高相关结果，可以补充颜色、地点、品牌或典型特征后再试。"
            :image-size="70"
          />
        </div>
      </div>
    </transition>

    <el-button class="assistant-trigger" type="primary" circle @click="visible = !visible">
      <el-icon size="20"><ChatDotRound /></el-icon>
    </el-button>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'

import ItemCard from '@/components/ItemCard.vue'
import { apiAssistantSearch } from '@/api'

const visible = ref(false)
const loading = ref(false)
const searched = ref(false)
const message = ref('')
const reply = ref('')
const filters = ref({})
const results = ref([])

const filtersSummary = computed(() => {
  const output = []
  if (filters.value.intent === 'lost') output.push('场景：找招领')
  if (filters.value.intent === 'found') output.push('场景：找失物')
  if (filters.value.category) output.push(`类别：${filters.value.category}`)
  if (filters.value.color) output.push(`颜色：${filters.value.color}`)
  if (filters.value.brand) output.push(`品牌：${filters.value.brand}`)
  if (filters.value.location) output.push(`地点：${filters.value.location}`)
  return output
})

function fillDemo() {
  message.value = '我今天上午在图书馆丢了一个黑色充电宝，表面有一点划痕，可能落在自习区附近。'
}

async function handleSearch() {
  if (!message.value.trim()) {
    ElMessage.warning('先输入一段物品描述再检索')
    return
  }

  loading.value = true
  searched.value = true
  try {
    const res = await apiAssistantSearch({
      message: message.value.trim(),
      limit: 5,
    })
    reply.value = res.reply || ''
    filters.value = res.filters || {}
    results.value = res.items || []
  } catch (error) {
    console.error(error)
    results.value = []
    reply.value = ''
    filters.value = {}
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.assistant-shell {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 1200;
}

.assistant-panel {
  position: absolute;
  right: 0;
  bottom: 72px;
  width: 420px;
  max-width: calc(100vw - 32px);
  max-height: min(76vh, 760px);
  overflow: hidden;
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, rgba(250, 204, 21, 0.18), transparent 28%),
    linear-gradient(160deg, #fffef8 0%, #fff 38%, #f6fbff 100%);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.18);
  backdrop-filter: blur(14px);
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px 18px 14px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

.panel-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.panel-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: #64748b;
}

.panel-body {
  padding: 16px 16px 18px;
  overflow-y: auto;
  max-height: calc(min(76vh, 760px) - 70px);
}

.prompt-box {
  margin-bottom: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(255, 247, 214, 0.9), rgba(243, 248, 255, 0.9));
}

.prompt-label {
  font-size: 12px;
  font-weight: 600;
  color: #92400e;
}

.prompt-example {
  margin-top: 4px;
  font-size: 13px;
  line-height: 1.6;
  color: #475569;
}

.panel-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 12px;
}

.assistant-reply {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 16px;
  background: #f8fafc;
  color: #334155;
  line-height: 1.7;
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.result-list {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-card {
  padding: 10px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.result-extra {
  padding: 4px 8px 2px;
}

.score-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: #475569;
}

.score-line b {
  color: #c2410c;
}

.reason-line {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.6;
  color: #64748b;
}

.assistant-trigger {
  width: 54px;
  height: 54px;
  border: none !important;
  box-shadow: 0 16px 32px rgba(249, 115, 22, 0.35);
  background: linear-gradient(135deg, #f97316 0%, #fb923c 100%) !important;
}

.assistant-trigger:hover {
  transform: translateY(-2px) scale(1.03);
}

.assistant-fade-enter-active,
.assistant-fade-leave-active {
  transition: all 0.25s ease;
}

.assistant-fade-enter-from,
.assistant-fade-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.98);
}

@media (max-width: 768px) {
  .assistant-shell {
    right: 16px;
    bottom: 16px;
  }

  .assistant-panel {
    width: min(420px, calc(100vw - 24px));
    right: -4px;
    bottom: 68px;
  }
}
</style>
