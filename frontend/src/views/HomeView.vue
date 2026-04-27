<template>
  <div class="home">
    <div class="hero">
      <div class="hero-bg-pattern"></div>
      <div class="hero-content">
        <div class="hero-icon">
          <el-icon size="48"><Search /></el-icon>
        </div>
        <h1>校园智能失物招领</h1>
        <p>从图像识别，到自然语言检索，再到 AI 快速发布，让寻物流程更轻、更快。</p>
        <div class="hero-actions">
          <el-button type="primary" size="large" class="hero-btn primary-btn" @click="router.push('/search')">
            <el-icon><Camera /></el-icon> 以图搜物
          </el-button>
          <el-button size="large" class="hero-btn" @click="router.push('/publish')">
            <el-icon><Plus /></el-icon> 发布信息
          </el-button>
          <el-button size="large" class="hero-btn" plain @click="router.push('/smart-search')">
            <el-icon><ChatDotRound /></el-icon> 智能寻物
          </el-button>
          <el-button size="large" class="hero-btn" plain @click="router.push('/quick-publish')">
            <el-icon><MagicStick /></el-icon> 快速发布
          </el-button>
        </div>
      </div>
    </div>

    <div class="stats-row">
      <div v-for="(stat, idx) in stats" :key="stat.label" class="stat-card">
        <div class="stat-icon" :class="`stat-icon-${idx}`">
          <el-icon size="24">
            <component :is="['LostFound', 'Found', 'CircleCheck'][idx]" />
          </el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-num">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <div class="feature-grid">
      <div class="feature-card">
        <div class="feature-title">智能寻物</div>
        <p>直接输入“我在教室丢了一个黑色小米充电宝”，AI 自动提取条件并返回相关招领信息。</p>
      </div>
      <div class="feature-card">
        <div class="feature-title">快速发布</div>
        <p>支持自然语言解析，把原本繁琐的表单填写流程压缩成一句描述。</p>
      </div>
      <div class="feature-card">
        <div class="feature-title">异步智能匹配</div>
        <p>后台结合图像、颜色、品牌和关键词进行综合评分，并主动推送疑似匹配结果。</p>
      </div>
    </div>

    <el-row :gutter="24" style="margin-top: 32px">
      <el-col :span="12">
        <div class="section-header">
          <span class="section-title">
            <el-icon class="section-icon lost-icon"><Warning /></el-icon>
            最新寻物
          </span>
          <el-link type="primary" class="view-all-link" @click="router.push('/items?type=lost')">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </el-link>
        </div>
        <ItemCard v-for="item in lostItems" :key="item.id" :item="item" />
        <el-empty v-if="!lostItems.length" description="暂无寻物信息" />
      </el-col>
      <el-col :span="12">
        <div class="section-header">
          <span class="section-title">
            <el-icon class="section-icon found-icon"><Star /></el-icon>
            最新招领
          </span>
          <el-link type="primary" class="view-all-link" @click="router.push('/items?type=found')">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </el-link>
        </div>
        <ItemCard v-for="item in foundItems" :key="item.id" :item="item" />
        <el-empty v-if="!foundItems.length" description="暂无招领信息" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { apiGetItems } from '@/api'
import ItemCard from '@/components/ItemCard.vue'

const router = useRouter()
const lostItems = ref([])
const foundItems = ref([])
const stats = ref([
  { label: '寻物信息', value: 0 },
  { label: '招领信息', value: 0 },
  { label: '成功认领', value: 0 },
])

onMounted(async () => {
  const [lostRes, foundRes, closedRes] = await Promise.all([
    apiGetItems({ type: 'lost', page_size: 4, exclude_closed: true }),
    apiGetItems({ type: 'found', page_size: 4, exclude_closed: true }),
    apiGetItems({ status: 'closed', page_size: 1 }),
  ])
  lostItems.value = lostRes.items || []
  foundItems.value = foundRes.items || []
  stats.value[0].value = lostRes.total || 0
  stats.value[1].value = foundRes.total || 0
  stats.value[2].value = closedRes.total || 0
})
</script>

<style scoped>
.home {
  animation: fadeInUp 0.6s ease-out;
}

.hero {
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  border-radius: 24px;
  padding: 56px 48px;
  text-align: center;
  color: #fff;
  margin-bottom: 28px;
  overflow: hidden;
}

.hero-bg-pattern {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.15) 0%, transparent 50%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-icon {
  width: 88px;
  height: 88px;
  margin: 0 auto 20px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.hero h1 {
  font-size: 36px;
  margin: 0 0 12px;
  font-weight: 700;
  letter-spacing: 1px;
}

.hero p {
  font-size: 16px;
  opacity: 0.92;
  margin: 0 0 32px;
  letter-spacing: 0.5px;
}

.hero-actions {
  display: flex;
  gap: 14px;
  justify-content: center;
  flex-wrap: wrap;
}

.hero-btn {
  padding: 12px 24px !important;
  font-size: 15px !important;
  border-radius: 12px !important;
  border: 2px solid rgba(255, 255, 255, 0.3) !important;
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
  backdrop-filter: blur(10px);
}

.hero-btn.primary-btn {
  background: linear-gradient(135deg, #fff 0%, #f0f0f0 100%) !important;
  color: #667eea !important;
  border: none !important;
  font-weight: 600;
}

.stats-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-icon-0 {
  background: linear-gradient(135deg, #ff6b6b, #ee5a5a);
}

.stat-icon-1 {
  background: linear-gradient(135deg, #51cf66, #40c057);
}

.stat-icon-2 {
  background: linear-gradient(135deg, #339af0, #228be6);
}

.stat-num {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

.feature-card {
  background: #fff;
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.feature-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.feature-card p {
  margin: 10px 0 0;
  line-height: 1.8;
  color: #6b7280;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.section-icon {
  padding: 6px;
  border-radius: 8px;
}

.lost-icon {
  background: rgba(255, 107, 107, 0.1);
  color: #ff6b6b;
}

.found-icon {
  background: rgba(81, 207, 102, 0.1);
  color: #51cf66;
}

.view-all-link {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
}

@media (max-width: 960px) {
  .stats-row,
  .feature-grid {
    grid-template-columns: 1fr;
    display: grid;
  }
}
</style>
