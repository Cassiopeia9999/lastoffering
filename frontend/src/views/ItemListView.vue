<template>
  <div>
    <!-- 搜索栏 -->
    <el-card class="search-bar" shadow="never">
      <el-row :gutter="12" align="middle">
        <el-col :span="8">
          <el-input v-model="filters.keyword" placeholder="搜索物品名称或描述..."
                    clearable prefix-icon="Search" @keyup.enter="doSearch" />
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.type" placeholder="类型" clearable style="width:100%">
            <el-option label="失物" value="lost" />
            <el-option label="招领" value="found" />
          </el-select>
        </el-col>
        <el-col :span="5">
          <el-select v-model="filters.category" placeholder="物品类别" clearable style="width:100%">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.status" placeholder="状态" clearable style="width:100%">
            <el-option label="待认领" value="pending" />
            <el-option label="已匹配" value="matched" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" style="width:100%" @click="doSearch">搜索</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 结果区 -->
    <div class="result-header">
      <span class="result-count">共 {{ total }} 条结果</span>
      <el-button type="primary" plain size="small" @click="router.push('/search')">
        <el-icon><Camera /></el-icon> 以图搜物
      </el-button>
    </div>

    <el-row :gutter="16" v-loading="loading">
      <el-col :xs="24" :sm="12" :md="8" v-for="item in items" :key="item.id">
        <ItemCard :item="item" />
      </el-col>
    </el-row>

    <el-empty v-if="!loading && !items.length" description="暂无匹配的物品信息" />

    <el-pagination v-if="total > pageSize" background layout="prev, pager, next"
                   :total="total" :page-size="pageSize" v-model:current-page="page"
                   @current-change="loadItems" style="margin-top:24px;justify-content:center;display:flex" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { apiGetItems, apiGetCategories } from '@/api'
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

onMounted(async () => {
  const catRes = await apiGetCategories()
  categories.value = catRes.categories
  loadItems()
})

watch(() => route.query.type, val => {
  filters.type = val || ''
  doSearch()
})
</script>

<style scoped>
.search-bar { margin-bottom: 16px; border-radius: 10px; }
.result-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 12px;
}
.result-count { color: #606266; font-size: 14px; }
</style>
