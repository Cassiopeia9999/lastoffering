<template>
  <div class="search-wrap">
    <el-card shadow="never" class="search-card">
      <template #header>
        <div style="display:flex;align-items:center;gap:8px">
          <el-icon size="20" color="#409eff"><Camera /></el-icon>
          <span style="font-size:16px;font-weight:600">以图搜物 · AI 智能匹配</span>
        </div>
      </template>

      <el-row :gutter="24">
        <!-- 左：上传区 -->
        <el-col :span="10">
          <div class="upload-zone" :class="{ 'has-image': previewUrl }"
               @click="triggerUpload" @dragover.prevent @drop.prevent="handleDrop">
            <img v-if="previewUrl" :src="previewUrl" class="preview-img" />
            <div v-else class="upload-placeholder">
              <el-icon size="48" color="#c0c4cc"><Upload /></el-icon>
              <p>点击或拖拽图片到此处</p>
              <p style="font-size:12px;color:#c0c4cc">支持 JPG / PNG / WEBP，最大 10MB</p>
            </div>
            <input ref="fileInput" type="file" accept="image/*" hidden @change="handleFileChange" />
          </div>

          <!-- AI 识别结果 -->
          <div v-if="aiResult" class="ai-result">
            <div class="ai-title"><el-icon><MagicStick /></el-icon> AI 识别结果</div>
            <div class="ai-cats">
              <el-tag v-for="c in aiResult.top_categories" :key="c.category"
                      :type="c === aiResult.top_categories[0] ? '' : 'info'"
                      style="margin:4px">
                {{ c.category }} {{ (c.confidence * 100).toFixed(0) }}%
              </el-tag>
            </div>
          </div>

          <div class="search-options">
            <el-radio-group v-model="searchType" style="margin-bottom:12px">
              <el-radio value="found">在招领库中查找</el-radio>
              <el-radio value="lost">在失物库中查找</el-radio>
            </el-radio-group>
            <el-slider v-model="threshold" :min="0" :max="1" :step="0.05"
                       :format-tooltip="v => `相似度 ≥ ${(v*100).toFixed(0)}%`" />
            <div style="font-size:12px;color:#909399;margin-top:4px">
              相似度阈值：{{ (threshold * 100).toFixed(0) }}%（占位模式建议设为 0%）
            </div>
            <el-button type="primary" size="large" :loading="searching"
                       :disabled="!imageFile" style="width:100%;margin-top:12px"
                       @click="doSearch">
              <el-icon><Search /></el-icon> 开始搜索
            </el-button>
            <el-button style="width:100%;margin-top:8px" @click="reset">重置</el-button>
          </div>
        </el-col>

        <!-- 右：搜索结果 -->
        <el-col :span="14">
          <div v-if="!searched" class="result-empty">
            <el-icon size="64" color="#e4e7ed"><PictureFilled /></el-icon>
            <p>上传图片后点击搜索，AI 将自动匹配相似物品</p>
          </div>

          <template v-else>
            <div class="result-header">
              <span>找到 <b>{{ results.length }}</b> 条相似物品</span>
            </div>

            <el-empty v-if="!results.length" description="未找到相似物品，可尝试降低相似度阈值或直接发布失物信息" />

            <div v-for="r in results" :key="r.item.id" class="result-item"
                 @click="router.push(`/items/${r.item.id}`)">
              <el-image v-if="r.item.image_url" :src="`/${r.item.image_url}`"
                        fit="cover" class="result-img" />
              <div v-else class="result-img-placeholder"><el-icon><Picture /></el-icon></div>
              <div class="result-info">
                <div class="result-title">{{ r.item.title }}</div>
                <div class="result-meta">
                  <el-tag size="small" :type="r.item.type === 'lost' ? 'danger' : 'success'">
                    {{ r.item.type === 'lost' ? '失物' : '招领' }}
                  </el-tag>
                  <el-tag size="small" effect="plain">{{ r.item.category }}</el-tag>
                  <span v-if="r.item.location" style="color:#909399;font-size:12px">
                    <el-icon><Location /></el-icon> {{ r.item.location }}
                  </span>
                </div>
              </div>
              <div class="result-sim">
                <el-progress type="circle" :percentage="+(r.similarity * 100).toFixed(0)"
                             :width="56" :stroke-width="5"
                             :color="simColor(r.similarity)" />
                <div style="font-size:11px;color:#909399;margin-top:4px">相似度</div>
              </div>
            </div>

            <!-- 未找到时引导发布 -->
            <el-alert v-if="results.length < 3" type="info" :closable="false"
                      style="margin-top:16px" show-icon>
              <template #title>没有找到满意的结果？</template>
              <el-button type="primary" link @click="router.push('/publish')">
                点击发布失物信息，等待拾得者主动联系你
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

function triggerUpload() { fileInput.value.click() }

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
  if (!imageFile.value) { ElMessage.warning('请先上传图片'); return }
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
  if (sim >= 0.8) return '#67c23a'
  if (sim >= 0.5) return '#e6a23c'
  return '#909399'
}
</script>

<style scoped>
.search-wrap { max-width: 1000px; margin: 0 auto; }
.upload-zone {
  border: 2px dashed #dcdfe6; border-radius: 12px; height: 260px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: border-color .2s; overflow: hidden;
  position: relative;
}
.upload-zone:hover { border-color: #409eff; }
.upload-zone.has-image { border-style: solid; }
.upload-placeholder { text-align: center; color: #909399; }
.upload-placeholder p { margin: 8px 0 0; }
.preview-img { width: 100%; height: 100%; object-fit: contain; }
.ai-result {
  margin-top: 12px; padding: 10px 14px; background: #f0f9eb;
  border-radius: 8px; border: 1px solid #b3e19d;
}
.ai-title { display: flex; align-items: center; gap: 6px; color: #67c23a; font-weight: 600; margin-bottom: 6px; }
.search-options { margin-top: 16px; }
.result-empty { text-align: center; padding: 60px 20px; color: #c0c4cc; }
.result-empty p { margin-top: 12px; font-size: 14px; }
.result-header { font-size: 14px; color: #606266; margin-bottom: 12px; }
.result-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px; border-radius: 10px; cursor: pointer;
  transition: background .15s; margin-bottom: 8px;
  border: 1px solid #ebeef5;
}
.result-item:hover { background: #f5f7fa; }
.result-img { width: 72px; height: 72px; border-radius: 8px; object-fit: cover; flex-shrink: 0; }
.result-img-placeholder {
  width: 72px; height: 72px; border-radius: 8px; background: #f5f7fa;
  display: flex; align-items: center; justify-content: center; color: #c0c4cc; flex-shrink: 0;
}
.result-info { flex: 1; min-width: 0; }
.result-title { font-size: 15px; font-weight: 600; color: #303133; margin-bottom: 6px; }
.result-meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.result-sim { text-align: center; flex-shrink: 0; }
</style>
