<template>
  <div class="search-wrap">
    <el-card shadow="never" class="search-card">
      <template #header>
        <div class="card-header">
          <div class="header-icon">
            <el-icon size="24"><Camera /></el-icon>
          </div>
          <div>
            <div class="header-title">以图搜图</div>
            <div class="header-subtitle">上传一张图片，系统会在失物或招领库中自动寻找相似物品。</div>
          </div>
        </div>
      </template>

      <el-row :gutter="24">
        <el-col :span="10">
          <div class="upload-zone" :class="{ 'has-image': previewUrl }" @click="triggerUpload" @dragover.prevent @drop.prevent="handleDrop">
            <img v-if="previewUrl" :src="previewUrl" class="preview-img" />
            <div v-else class="upload-placeholder">
              <div class="upload-icon">
                <el-icon size="48"><Upload /></el-icon>
              </div>
              <p class="upload-text">点击或拖拽图片到此处</p>
              <p class="upload-hint">支持 JPG / PNG / WEBP，最大 10MB</p>
            </div>
            <input ref="fileInput" type="file" accept="image/*" hidden @change="handleFileChange" />
          </div>

          <div v-if="aiResult" class="ai-result">
            <div class="ai-title">
              <el-icon><MagicStick /></el-icon>
              AI 识别结果
            </div>
            <div class="ai-cats">
              <el-tag
                v-for="c in aiResult.top_categories"
                :key="c.category"
                :type="c === aiResult.top_categories[0] ? 'primary' : 'info'"
                class="ai-tag"
                round
              >
                {{ c.category }} {{ (c.confidence * 100).toFixed(0) }}%
              </el-tag>
            </div>
          </div>

          <div class="search-options">
            <div class="option-card">
              <div class="option-title">检索方向</div>
              <el-radio-group v-model="searchType" class="search-type-group">
                <el-radio value="found">在招领库中查找</el-radio>
                <el-radio value="lost">在失物库中查找</el-radio>
              </el-radio-group>
            </div>

            <div class="option-card">
              <div class="option-title">相似度阈值</div>
              <el-slider v-model="threshold" :min="0" :max="1" :step="0.05" :format-tooltip="(v) => `相似度 ≥ ${(v * 100).toFixed(0)}%`" />
              <div class="threshold-hint">当前阈值：{{ (threshold * 100).toFixed(0) }}%</div>
            </div>

            <el-button type="primary" size="large" :loading="searching" :disabled="!imageFile" class="search-btn" @click="doSearch">
              <el-icon><Search /></el-icon>
              开始搜索
            </el-button>
            <el-button size="large" class="reset-btn" @click="reset">重置</el-button>
          </div>
        </el-col>

        <el-col :span="14">
          <div v-if="!searched" class="result-empty">
            <div class="empty-icon">
              <el-icon size="64"><PictureFilled /></el-icon>
            </div>
            <p>上传图片后点击搜索，系统会自动匹配相似物品。</p>
          </div>

          <template v-else>
            <div class="result-header">
              <span>找到 <b class="result-count">{{ results.length }}</b> 条相似物品</span>
            </div>

            <el-empty v-if="!results.length" description="未找到相似物品，可以尝试调低阈值或直接发布信息" />

            <div v-for="r in results" :key="r.item.id" class="result-item" @click="router.push(`/items/${r.item.id}`)">
              <el-image v-if="r.item.image_url" :src="`/${r.item.image_url}`" fit="cover" class="result-img" />
              <div v-else class="result-img-placeholder"><el-icon><Picture /></el-icon></div>
              <div class="result-info">
                <div class="result-title">{{ r.item.title }}</div>
                <div class="result-meta">
                  <span class="meta-pill" :class="r.item.type === 'lost' ? 'meta-pill-lost' : 'meta-pill-found'">
                    {{ r.item.type === 'lost' ? '失物' : '招领' }}
                  </span>
                  <span v-if="r.item.category" class="meta-pill meta-pill-category">{{ r.item.category }}</span>
                  <span v-if="r.item.location" class="result-location">
                    <el-icon><Location /></el-icon>
                    {{ r.item.location }}
                  </span>
                </div>
              </div>
              <div class="result-sim">
                <el-progress
                  type="circle"
                  :percentage="+(r.similarity * 100).toFixed(0)"
                  :width="58"
                  :stroke-width="5"
                  :color="simColor(r.similarity)"
                />
                <div class="sim-label">相似度</div>
              </div>
            </div>

            <el-alert v-if="results.length < 3" type="info" :closable="false" class="publish-hint" show-icon>
              <template #title>没有找到满意的结果？</template>
              <el-button type="primary" link @click="router.push('/publish')">
                点击发布失物信息，等待捡到者主动联系你
              </el-button>
            </el-alert>
          </template>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Camera, Location, MagicStick, Picture, PictureFilled, Search, Upload } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { apiSearchByImage } from '@/api'

const router = useRouter()
const fileInput = ref()
const imageFile = ref(null)
const previewUrl = ref('')
const searching = ref(false)
const searched = ref(false)
const results = ref([])
const aiResult = ref(null)
const searchType = ref('found')
const threshold = ref(0)

function triggerUpload() {
  fileInput.value.click()
}

function handleFileChange(e) {
  const file = e.target.files[0]
  if (file) setImage(file)
}

function handleDrop(e) {
  const file = e.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) setImage(file)
}

function setImage(file) {
  imageFile.value = file
  previewUrl.value = URL.createObjectURL(file)
  searched.value = false
  aiResult.value = null
}

async function doSearch() {
  if (!imageFile.value) {
    ElMessage.warning('请先上传图片')
    return
  }
  searching.value = true
  try {
    const fd = new FormData()
    fd.append('image', imageFile.value)
    fd.append('search_type', searchType.value)
    fd.append('top_k', 10)
    fd.append('threshold', threshold.value)
    const res = await apiSearchByImage(fd)
    aiResult.value = res
    results.value = res.results
    searched.value = true
  } finally {
    searching.value = false
  }
}

function reset() {
  imageFile.value = null
  previewUrl.value = ''
  searched.value = false
  results.value = []
  aiResult.value = null
  fileInput.value.value = ''
}

function simColor(sim) {
  if (sim >= 0.8) return '#16a34a'
  if (sim >= 0.5) return '#ea580c'
  return '#64748b'
}
</script>

<style scoped>
.search-wrap {
  max-width: 1100px;
  margin: 0 auto;
}

.search-card {
  border-radius: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  color: #fff;
  border-radius: 16px;
  background: linear-gradient(135deg, #2563eb, #0f172a);
}

.header-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.header-subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: #64748b;
}

.upload-zone {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 280px;
  overflow: hidden;
  cursor: pointer;
  border: 2px dashed #dbe4f0;
  border-radius: 20px;
  background: linear-gradient(135deg, #f8fbff, #fffdf8);
  transition: all 0.25s ease;
}

.upload-zone:hover {
  border-color: #2563eb;
  transform: translateY(-1px);
}

.upload-zone.has-image {
  border-style: solid;
  border-color: #16a34a;
}

.upload-placeholder {
  padding: 20px;
  text-align: center;
}

.upload-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 88px;
  height: 88px;
  margin: 0 auto 16px;
  color: #fff;
  border-radius: 22px;
  background: linear-gradient(135deg, #2563eb, #0f172a);
}

.upload-text {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.upload-hint {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.ai-result,
.option-card {
  margin-top: 16px;
  padding: 16px;
  border-radius: 16px;
}

.ai-result {
  border: 1px solid #bbf7d0;
  background: linear-gradient(135deg, #f0fdf4, #ecfeff);
}

.ai-title,
.option-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.ai-tag {
  margin: 4px 6px 0 0;
}

.search-options {
  margin-top: 20px;
}

.option-card {
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: #fff;
}

.search-type-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.threshold-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #64748b;
}

.search-btn,
.reset-btn {
  width: 100%;
  height: 46px;
  margin-top: 14px;
  border-radius: 14px !important;
}

.search-btn {
  border: none !important;
  background: linear-gradient(135deg, #2563eb, #0f172a) !important;
}

.result-empty {
  padding: 86px 20px;
  color: #94a3b8;
  text-align: center;
}

.empty-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 120px;
  margin: 0 auto 20px;
  border-radius: 26px;
  background: linear-gradient(135deg, #f3f6fb, #eaf0f8);
}

.result-header {
  margin-bottom: 16px;
  font-size: 15px;
  color: #475569;
}

.result-count {
  color: #2563eb;
  font-size: 18px;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
  padding: 16px;
  cursor: pointer;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 18px;
  background: linear-gradient(135deg, #fff, #fbfdff);
  transition: all 0.25s ease;
}

.result-item:hover {
  transform: translateX(4px);
  border-color: rgba(37, 99, 235, 0.24);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
}

.result-img,
.result-img-placeholder {
  width: 84px;
  height: 84px;
  flex-shrink: 0;
  border-radius: 14px;
}

.result-img-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  background: linear-gradient(135deg, #f3f6fb, #eaf0f8);
}

.result-info {
  flex: 1;
  min-width: 0;
}

.result-title {
  margin-bottom: 8px;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.meta-pill {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.meta-pill-lost {
  color: #b91c1c;
  background: #fee2e2;
}

.meta-pill-found {
  color: #166534;
  background: #dcfce7;
}

.meta-pill-category {
  color: #7c3aed;
  background: #ede9fe;
}

.result-location {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: #64748b;
}

.result-sim {
  flex-shrink: 0;
  text-align: center;
}

.sim-label {
  margin-top: 6px;
  font-size: 12px;
  color: #64748b;
}

.publish-hint {
  margin-top: 18px;
  border-radius: 16px;
}
</style>
