<template>
  <div class="list-page">
    <section class="toolbar">
      <div class="toolbar-copy">
        <p class="eyebrow">物品列表</p>
        <h1>按条件筛选校园失物与招领信息</h1>
      </div>

      <el-card class="search-bar" shadow="never">
        <el-row :gutter="14" align="middle">
          <el-col :xl="8" :lg="8" :md="24" :sm="24">
            <el-input
              v-model="filters.keyword"
              placeholder="搜索物品名称、描述或关键词"
              clearable
              @keyup.enter="doSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :xl="4" :lg="4" :md="8" :sm="12" :xs="24">
            <el-select v-model="filters.type" placeholder="类型" clearable style="width: 100%">
              <el-option label="失物" value="lost" />
              <el-option label="招领" value="found" />
            </el-select>
          </el-col>
          <el-col :xl="5" :lg="5" :md="8" :sm="12" :xs="24">
            <el-select v-model="filters.category" placeholder="物品类别" clearable style="width: 100%">
              <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
            </el-select>
          </el-col>
          <el-col :xl="4" :lg="4" :md="8" :sm="12" :xs="24">
            <el-select v-model="filters.status" placeholder="状态" clearable style="width: 100%">
              <el-option label="待处理" value="pending" />
              <el-option label="已匹配" value="matched" />
              <el-option label="已完成" value="closed" />
            </el-select>
          </el-col>
          <el-col :xl="3" :lg="3" :md="24" :sm="12" :xs="24">
            <div class="action-row">
              <el-button type="primary" class="action-btn" @click="doSearch">搜索</el-button>
              <el-button class="action-btn soft-btn" @click="resetFilters">重置</el-button>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </section>

    <section class="result-shell">
      <div class="result-header">
        <div>
          <div class="result-title">检索结果</div>
          <div class="result-count">共 {{ total }} 条记录</div>
        </div>
        <el-button type="primary" plain class="image-btn" @click="router.push('/search')">
          <el-icon><Camera /></el-icon>
          以图搜图
        </el-button>
      </div>

      <el-row :gutter="18" v-loading="loading">
        <el-col :xs="24" :sm="12" :md="8" v-for="item in items" :key="item.id">
          <ItemCard :item="item" />
        </el-col>
      </el-row>

      <el-empty v-if="!loading && !items.length" description="暂时没有符合条件的物品信息" />

      <el-pagination
        v-if="total > pageSize"
        background
        layout="prev, pager, next"
        :total="total"
        :page-size="pageSize"
        v-model:current-page="page"
        @current-change="loadItems"
        class="pager"
      />
    </section>
  </div>
</template>

<script setup>
import { reactive, onMounted, ref, watch } from 'vue'
import { Camera, Search } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'

import { apiGetCategories, apiGetItems } from '@/api'
import ItemCard from '@/components/ItemCard.vue'

const router = useRouter()
const route = useRoute()
const items = ref([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const pageSize = 12
const categories = ref([])

const filters = reactive({
  keyword: '',
  type: route.query.type || '',
  category: '',
  status: '',
})

async function loadItems() {
  loading.value = true
  try {
    const res = await apiGetItems({
      ...filters,
      page: page.value,
      page_size: pageSize,
    })
    items.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function doSearch() {
  page.value = 1
  loadItems()
}

function resetFilters() {
  filters.keyword = ''
  filters.type = route.query.type || ''
  filters.category = ''
  filters.status = ''
  doSearch()
}

onMounted(async () => {
  const catRes = await apiGetCategories()
  categories.value = catRes.categories
  loadItems()
})

watch(() => route.query.type, (val) => {
  filters.type = val || ''
  doSearch()
})
</script>

<style scoped>
.list-page {
  max-width: 1240px;
  margin: 0 auto;
}

.toolbar {
  margin-bottom: 22px;
}

.toolbar-copy {
  margin-bottom: 14px;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #2563eb;
}

.toolbar-copy h1 {
  margin: 0;
  font-size: 30px;
  color: #0f172a;
}

.search-bar {
  border-radius: 22px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: linear-gradient(135deg, #ffffff, #f8fbff);
}

.action-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.action-btn {
  width: 100%;
}

.soft-btn {
  border-color: #dbe4f0;
}

.result-shell {
  padding: 18px 0 8px;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.result-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.result-count {
  margin-top: 4px;
  font-size: 13px;
  color: #64748b;
}

.image-btn {
  border-radius: 999px;
}

.pager {
  display: flex;
  justify-content: center;
  margin-top: 28px;
}

:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  min-height: 44px;
  border-radius: 14px !important;
  box-shadow: none !important;
}

:deep(.el-input__wrapper.is-focus),
:deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
}

:deep(.el-pagination .el-pager li) {
  margin: 0 3px;
  border-radius: 10px;
}

:deep(.el-pagination .el-pager li.is-active) {
  background: linear-gradient(135deg, #2563eb, #0f172a);
}
</style>
