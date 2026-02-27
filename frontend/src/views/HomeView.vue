<template>
  <div class="home">
    <!-- Hero 区域 -->
    <div class="hero">
      <h1>校园智能失物招领</h1>
      <p>上传图片，AI 自动识别并匹配，快速找回失物</p>
      <div class="hero-actions">
        <el-button type="primary" size="large" @click="router.push('/search')">
          <el-icon><Camera /></el-icon> 以图搜物
        </el-button>
        <el-button size="large" @click="router.push('/publish')">
          <el-icon><Plus /></el-icon> 发布信息
        </el-button>
        <el-button size="large" plain @click="router.push('/items')">
          <el-icon><List /></el-icon> 浏览全部
        </el-button>
      </div>
    </div>

    <!-- 统计数字 -->
    <div class="stats-row">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-num">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <!-- 最新失物 / 招领 -->
    <el-row :gutter="24" style="margin-top:32px">
      <el-col :span="12">
        <div class="section-header">
          <span class="section-title">最新失物</span>
          <el-link type="primary" @click="router.push('/items?type=lost')">查看全部</el-link>
        </div>
        <ItemCard v-for="item in lostItems" :key="item.id" :item="item" />
        <el-empty v-if="!lostItems.length" description="暂无失物信息" />
      </el-col>
      <el-col :span="12">
        <div class="section-header">
          <span class="section-title">最新招领</span>
          <el-link type="primary" @click="router.push('/items?type=found')">查看全部</el-link>
        </div>
        <ItemCard v-for="item in foundItems" :key="item.id" :item="item" />
        <el-empty v-if="!foundItems.length" description="暂无招领信息" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiGetItems } from '@/api'
import ItemCard from '@/components/ItemCard.vue'

const router = useRouter()
const lostItems = ref([])
const foundItems = ref([])
const stats = ref([
  { label: '失物信息', value: 0 },
  { label: '招领信息', value: 0 },
  { label: '成功认领', value: 0 },
])

onMounted(async () => {
  const [lostRes, foundRes] = await Promise.all([
    apiGetItems({ type: 'lost', page_size: 4 }),
    apiGetItems({ type: 'found', page_size: 4 }),
  ])
  lostItems.value = lostRes.items
  foundItems.value = foundRes.items
  stats.value[0].value = lostRes.total
  stats.value[1].value = foundRes.total

  const allRes = await apiGetItems({ status: 'matched', page_size: 1 })
  stats.value[2].value = allRes.total
})
</script>

<style scoped>
.hero {
  background: linear-gradient(135deg, #1a6fc4, #2d8cf0);
  border-radius: 16px; padding: 48px 40px; text-align: center;
  color: #fff; margin-bottom: 24px;
}
.hero h1 { font-size: 32px; margin: 0 0 12px; }
.hero p { font-size: 16px; opacity: 0.9; margin: 0 0 28px; }
.hero-actions { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }

.stats-row {
  display: flex; gap: 16px; margin-bottom: 8px;
}
.stat-card {
  flex: 1; background: #fff; border-radius: 12px;
  padding: 20px; text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.stat-num { font-size: 32px; font-weight: 700; color: #409eff; }
.stat-label { font-size: 14px; color: #909399; margin-top: 4px; }

.section-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 12px;
}
.section-title { font-size: 16px; font-weight: 600; color: #303133; }
</style>
