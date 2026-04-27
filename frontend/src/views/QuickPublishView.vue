<template>
  <div class="quick-publish-page">
    <section class="hero">
      <div>
        <p class="eyebrow">快速发布</p>
        <h1>说一句话，系统先帮你把表单整理出来</h1>
        <p class="hero-text">
          支持直接输入物品描述。系统会先进行本地快速提取，再通过 AI 做增强补全，最后由你确认后发布。
        </p>
      </div>
    </section>

    <el-row :gutter="24">
      <el-col :lg="9" :md="10" :sm="24">
        <el-card shadow="never" class="input-panel">
          <div class="panel-title">描述你的物品情况</div>

          <div class="example-box">
            <div class="example-label">输入示例</div>
            <div class="example-text">{{ activeExample }}</div>
            <div class="example-actions">
              <el-button text @click="prevExample">上一条</el-button>
              <el-button text @click="nextExample">下一条</el-button>
            </div>
          </div>

          <el-form label-position="top">
            <el-form-item label="自然语言描述">
              <el-input
                v-model="message"
                type="textarea"
                :rows="8"
                resize="none"
                maxlength="400"
                show-word-limit
                placeholder="例如：我昨天下午在教学楼丢了一个黑色小米充电宝，外壳有划痕，可能落在教室里。"
              />
            </el-form-item>
          </el-form>

          <transition name="fade-slide">
            <div v-if="stageVisible" class="stage-box">
              <div class="stage-head">
                <span class="stage-dot" :class="parseStage" />
                <strong>{{ stageTitle }}</strong>
              </div>
              <p class="stage-text">{{ stageText }}</p>
              <div class="runtime-strip">
                <div class="runtime-card runtime-card-local" :class="{ active: parseStage === 'fast' }">
                  <div class="runtime-label">本地快速</div>
                  <div class="runtime-value">{{ localDisplayTime }}</div>
                </div>
                <div class="runtime-card runtime-card-ai" :class="{ active: parseStage === 'full' }">
                  <div class="runtime-label">AI 增强</div>
                  <div class="runtime-value">{{ aiDisplayTime }}</div>
                </div>
              </div>
            </div>
          </transition>

          <div v-if="versionOptions.length" class="version-box">
            <div class="version-title">解析版本</div>
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

          <div class="panel-actions">
            <el-button @click="fillDemo">填入示例</el-button>
            <el-button type="primary" :loading="parsing" @click="handleParse">开始解析</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :lg="15" :md="14" :sm="24">
        <el-card shadow="never" class="form-panel">
          <template #header>
            <div class="result-header">
              <span>发布表单</span>
              <div class="header-right">
                <span v-if="selectedVersionBadge" class="selected-badge" :class="selectedVersion">
                  {{ selectedVersionBadge }}
                </span>
              </div>
            </div>
          </template>

          <div v-if="parsedPreview" class="preview-summary">
            <div class="preview-title">解析预览</div>
            <div class="preview-tags">
              <el-tag effect="dark" round>{{ parsedPreview.type === 'found' ? '招领' : '寻物' }}</el-tag>
              <el-tag v-if="parsedPreview.category" effect="plain" round>{{ parsedPreview.category }}</el-tag>
              <el-tag v-if="parsedPreview.color" effect="plain" round>{{ parsedPreview.color }}</el-tag>
              <el-tag v-if="parsedPreview.brand" effect="plain" round>{{ parsedPreview.brand }}</el-tag>
              <el-tag v-if="parsedPreview.location" effect="plain" round>{{ parsedPreview.location }}</el-tag>
            </div>
            <div v-if="parsedPreview.feature_text" class="preview-text">
              典型特征：{{ parsedPreview.feature_text }}
            </div>
          </div>

          <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" class="publish-form">
            <el-form-item label="信息类型" prop="type">
              <el-radio-group v-model="form.type">
                <el-radio-button value="lost">寻物</el-radio-button>
                <el-radio-button value="found">招领</el-radio-button>
              </el-radio-group>
              <div class="field-tip">系统会先自动判断失物或招领，你也可以手动修改。</div>
            </el-form-item>

            <el-form-item label="物品图片">
              <div class="upload-area">
                <div v-if="imagePreview" class="image-preview-container">
                  <img :src="imagePreview" class="preview-image" />
                  <div class="image-actions">
                    <el-button circle size="small" @click="reCropImage">
                      <el-icon><Crop /></el-icon>
                    </el-button>
                    <el-button circle size="small" type="danger" @click="handleImageRemove">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
                <el-upload
                  v-else
                  :auto-upload="false"
                  :show-file-list="false"
                  :limit="1"
                  accept="image/*"
                  list-type="picture-card"
                  :on-change="handleImageChange"
                >
                  <el-icon><Plus /></el-icon>
                </el-upload>
              </div>
            </el-form-item>

            <el-form-item label="标题" prop="title">
              <el-input v-model="form.title" placeholder="例如：黑色小米充电宝" />
            </el-form-item>

            <el-form-item label="类别">
              <el-select v-model="form.category" clearable placeholder="请选择类别" style="width: 100%">
                <el-option v-for="category in categories" :key="category" :label="category" :value="category" />
              </el-select>
            </el-form-item>

            <el-form-item label="颜色">
              <el-input v-model="form.color" clearable />
            </el-form-item>

            <el-form-item label="品牌">
              <el-input v-model="form.brand" clearable />
            </el-form-item>

            <el-form-item label="关键词">
              <div class="keyword-editor">
                <div class="keyword-tags">
                  <el-tag
                    v-for="keyword in form.keywords"
                    :key="keyword"
                    closable
                    effect="dark"
                    round
                    @close="removeKeyword(keyword)"
                  >
                    {{ keyword }}
                  </el-tag>
                  <span v-if="!form.keywords.length" class="keyword-placeholder">还没有关键词，可以手动补充。</span>
                </div>
                <div class="keyword-input-row">
                  <el-input
                    v-model="keywordInput"
                    placeholder="输入关键词后按回车或点击添加"
                    @keyup.enter="addKeyword"
                  />
                  <el-button @click="addKeyword">添加</el-button>
                </div>
                <div class="field-tip">AI 解析出的关键词会先填进来，你可以继续手动新增、删除或改写。</div>
              </div>
            </el-form-item>

            <el-form-item label="典型特征">
              <el-input v-model="form.feature_text" type="textarea" :rows="3" />
            </el-form-item>

            <el-form-item label="详细描述">
              <el-input v-model="form.description" type="textarea" :rows="4" />
            </el-form-item>

            <el-form-item label="地点">
              <el-input v-model="form.location" clearable />
            </el-form-item>

            <el-form-item label="时间">
              <el-date-picker v-model="form.happen_time" type="datetime" style="width: 100%" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="submitting" @click="handleSubmit">发布信息</el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showCropper" title="裁剪图片" width="720px" :close-on-click-modal="false">
      <div v-if="cropImageSrc" class="cropper-wrapper">
        <img ref="cropperImg" :src="cropImageSrc" class="cropper-image" />
      </div>
      <template #footer>
        <el-button @click="cancelCrop">取消</el-button>
        <el-button @click="skipCrop">跳过裁剪</el-button>
        <el-button type="primary" @click="confirmCrop">确认裁剪</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Crop, Delete, Plus } from '@element-plus/icons-vue'
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'

import { apiClassifyImage, apiCreateItem, apiGetCategories, apiQuickPublishParse } from '@/api'

const router = useRouter()
const formRef = ref()
const parsing = ref(false)
const submitting = ref(false)
const categories = ref([])
const imageFile = ref(null)
const imagePreview = ref('')
const keywordInput = ref('')
const showCropper = ref(false)
const cropImageSrc = ref('')
const cropFileName = ref('')
const pendingFile = ref(null)
const cropperImg = ref(null)
let cropper = null

const parseStage = ref('idle')
const fastElapsedMs = ref(null)
const fullElapsedMs = ref(null)
const liveElapsedMs = ref(0)
const localParse = ref(null)
const aiParse = ref(null)
const selectedVersion = ref('local')

let stageTimer = null
let stageStartedAt = 0

const examples = [
  '我今天在教学楼丢了一个黑色小米充电宝，外壳有划痕。',
  '我在操场附近捡到一个白色充电器，看起来像20W快充。',
  '我在食堂捡到一副红米耳机，外壳是青色的。',
  '我昨天下午在图书馆丢了一本笔记本，封面是蓝色的。',
  '我在宿舍楼下捡到一把钥匙，上面有卡通挂件。',
  '我在教学楼1407丢了一个包，里面有文具和充电器。',
]
const activeExampleIndex = ref(0)
const activeExample = computed(() => examples[activeExampleIndex.value])
const message = ref('')

const form = reactive({
  type: 'lost',
  title: '',
  category: '',
  color: '',
  brand: '',
  keywords: [],
  feature_text: '',
  description: '',
  location: '',
  happen_time: null,
})

const rules = {
  type: [{ required: true, message: '请选择信息类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
}

const stageVisible = computed(() => parseStage.value !== 'idle' || fastElapsedMs.value !== null || fullElapsedMs.value !== null)

const stageTitle = computed(() => {
  if (parseStage.value === 'fast') return '本地模型正在快速解析'
  if (parseStage.value === 'full') return 'AI 正在补全发布字段'
  if (fullElapsedMs.value !== null) return 'AI 增强解析已完成'
  if (fastElapsedMs.value !== null) return '本地快速解析已完成'
  return ''
})

const stageText = computed(() => {
  if (parseStage.value === 'fast') return '系统会先提取类别、颜色、地点、品牌、关键词等基础字段。'
  if (parseStage.value === 'full') return '系统正在结合大模型补全标题、典型特征和更自然的描述。'
  if (fullElapsedMs.value !== null) return '你可以在本地快速版和 AI 增强版之间切换，并决定采用哪一版。'
  if (fastElapsedMs.value !== null) return '本地解析已完成，系统正在继续生成 AI 增强版。'
  return ''
})

const versionOptions = computed(() => {
  const options = []
  if (localParse.value) options.push({ value: 'local', label: '本地快速版' })
  if (aiParse.value) options.push({ value: 'ai', label: 'AI 增强版' })
  return options
})

const currentParse = computed(() => {
  if (selectedVersion.value === 'ai' && aiParse.value) return aiParse.value
  if (localParse.value) return localParse.value
  return aiParse.value
})

const parsedPreview = computed(() => currentParse.value)

const selectedVersionBadge = computed(() => {
  if (selectedVersion.value === 'ai' && aiParse.value) return '当前显示：AI 增强版'
  if (selectedVersion.value === 'local' && localParse.value) return '当前显示：本地快速版'
  return ''
})

const selectedVersionTip = computed(() => {
  if (selectedVersion.value === 'ai' && aiParse.value) {
    return `AI 增强版会补充标题、典型特征和语义描述，耗时 ${formatElapsed(fullElapsedMs.value)}`
  }
  if (localParse.value) {
    return `本地快速版会优先提取结构化字段，耗时 ${formatElapsed(fastElapsedMs.value)}`
  }
  return ''
})

const localDisplayTime = computed(() => {
  if (parseStage.value === 'fast') return formatElapsed(liveElapsedMs.value)
  return fastElapsedMs.value !== null ? formatElapsed(fastElapsedMs.value) : '--'
})

const aiDisplayTime = computed(() => {
  if (parseStage.value === 'full') return formatElapsed(liveElapsedMs.value)
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

function addKeyword() {
  const value = keywordInput.value.trim()
  if (!value) return
  if (!form.keywords.includes(value)) {
    form.keywords.push(value)
  }
  keywordInput.value = ''
}

function removeKeyword(keyword) {
  form.keywords = form.keywords.filter((item) => item !== keyword)
}

function initCropper() {
  if (cropper) {
    cropper.destroy()
    cropper = null
  }
  if (!cropperImg.value || !cropImageSrc.value) return

  const createCropper = () => {
    cropper = new Cropper(cropperImg.value, {
      viewMode: 1,
      autoCropArea: 0.82,
      responsive: true,
    })
  }

  if (cropperImg.value.complete) {
    createCropper()
  } else {
    cropperImg.value.onload = createCropper
  }
}

watch(showCropper, (visible) => {
  if (visible && cropImageSrc.value) {
    nextTick(initCropper)
  } else if (!visible && cropper) {
    cropper.destroy()
    cropper = null
  }
})

function applyParseResult(res) {
  if (!res) return
  Object.assign(form, {
    type: res.type || form.type || 'lost',
    title: res.title || '',
    category: res.category || '',
    color: res.color || '',
    brand: res.brand || '',
    keywords: Array.isArray(res.keywords) ? res.keywords : [],
    feature_text: res.feature_text || '',
    description: res.description || message.value.trim(),
    location: res.location || '',
  })
}

watch(currentParse, (value) => {
  applyParseResult(value)
})

watch(versionOptions, (options) => {
  if (!options.some((item) => item.value === selectedVersion.value) && options.length) {
    selectedVersion.value = options[options.length - 1].value
  }
})

function prevExample() {
  activeExampleIndex.value = (activeExampleIndex.value - 1 + examples.length) % examples.length
}

function nextExample() {
  activeExampleIndex.value = (activeExampleIndex.value + 1) % examples.length
}

function fillDemo() {
  message.value = activeExample.value
}

async function classifyCurrentFile(file) {
  const formData = new FormData()
  formData.append('image', file)
  try {
    const res = await apiClassifyImage(formData)
    if (!form.category && res?.suggested_category) {
      form.category = res.suggested_category
    }
  } catch {
    // 保留手动流程
  }
}

function handleImageChange(file) {
  const reader = new FileReader()
  reader.onload = (event) => {
    cropImageSrc.value = event.target.result
    cropFileName.value = file.raw.name
    pendingFile.value = file.raw
    showCropper.value = true
  }
  reader.readAsDataURL(file.raw)
}

function confirmCrop() {
  if (!cropper) return
  cropper.getCroppedCanvas({
    width: 224,
    height: 224,
    fillColor: '#fff',
    imageSmoothingEnabled: true,
    imageSmoothingQuality: 'high',
  }).toBlob(async (blob) => {
    const croppedFile = new File([blob], cropFileName.value, { type: 'image/jpeg' })
    imageFile.value = croppedFile
    imagePreview.value = URL.createObjectURL(blob)
    showCropper.value = false
    await classifyCurrentFile(croppedFile)
  }, 'image/jpeg', 0.92)
}

async function skipCrop() {
  if (!pendingFile.value) return
  imageFile.value = pendingFile.value
  imagePreview.value = cropImageSrc.value
  showCropper.value = false
  await classifyCurrentFile(pendingFile.value)
}

function cancelCrop() {
  showCropper.value = false
  pendingFile.value = null
  cropImageSrc.value = ''
  cropFileName.value = ''
}

function handleImageRemove() {
  imageFile.value = null
  imagePreview.value = ''
  pendingFile.value = null
  cropImageSrc.value = ''
  cropFileName.value = ''
}

function reCropImage() {
  if (!imagePreview.value) return
  cropImageSrc.value = imagePreview.value
  showCropper.value = true
}

async function handleParse() {
  const trimmed = message.value.trim()
  if (!trimmed) {
    ElMessage.warning('请输入要解析的物品描述')
    return
  }

  parsing.value = true
  parseStage.value = 'idle'
  fastElapsedMs.value = null
  fullElapsedMs.value = null
  localParse.value = null
  aiParse.value = null
  selectedVersion.value = 'local'

  try {
    parseStage.value = 'fast'
    startStageTimer()
    const fastStarted = performance.now()
    const fastRes = await apiQuickPublishParse({
      message: trimmed,
      fast_only: true,
    })
    fastElapsedMs.value = performance.now() - fastStarted
    localParse.value = fastRes
    selectedVersion.value = 'local'
    stopStageTimer()

    parseStage.value = 'full'
    startStageTimer()
    const fullStarted = performance.now()
    const fullRes = await apiQuickPublishParse({
      message: trimmed,
      type: localParse.value?.type || form.type,
    })
    fullElapsedMs.value = performance.now() - fullStarted
    aiParse.value = fullRes
    selectedVersion.value = 'ai'
    stopStageTimer()

    ElMessage.success('解析完成，你可以确认字段后直接发布')
  } catch (error) {
    console.error('[QuickPublish] request failed', error)
    ElMessage.error(error?.response?.data?.detail || error?.message || '快速发布解析失败')
  } finally {
    stopStageTimer()
    parseStage.value = 'idle'
    parsing.value = false
  }
}

async function handleSubmit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    const formData = new FormData()
    formData.append('type', form.type)
    formData.append('title', form.title)
    if (form.category) formData.append('category', form.category)
    if (form.color) formData.append('color', form.color)
    if (form.brand) formData.append('brand', form.brand)
    if (form.keywords.length) formData.append('keywords', JSON.stringify(form.keywords))
    if (form.feature_text) formData.append('feature_text', form.feature_text)
    if (form.description) formData.append('description', form.description)
    if (form.location) formData.append('location', form.location)
    if (form.happen_time) formData.append('happen_time', new Date(form.happen_time).toISOString())
    if (imageFile.value) formData.append('image', imageFile.value)

    const item = await apiCreateItem(formData)
    ElMessage.success('发布成功')
    router.push(`/items/${item.id}`)
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  Object.assign(form, {
    type: 'lost',
    title: '',
    category: '',
    color: '',
    brand: '',
    keywords: [],
    feature_text: '',
    description: '',
    location: '',
    happen_time: null,
  })
  imageFile.value = null
  imagePreview.value = ''
  parseStage.value = 'idle'
  fastElapsedMs.value = null
  fullElapsedMs.value = null
  localParse.value = null
  aiParse.value = null
  selectedVersion.value = 'local'
  keywordInput.value = ''
  message.value = ''
}

onMounted(async () => {
  const res = await apiGetCategories()
  categories.value = res.categories || []
})

onBeforeUnmount(() => {
  stopStageTimer()
  if (cropper) {
    cropper.destroy()
    cropper = null
  }
})
</script>

<style scoped>
.quick-publish-page {
  max-width: 1240px;
  margin: 0 auto;
  animation: fadeInUp 0.5s ease-out;
}

.hero {
  margin-bottom: 22px;
  padding: 30px 32px;
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(56, 189, 248, 0.18), transparent 22%),
    linear-gradient(140deg, #eef9ff 0%, #ffffff 42%, #fff6ea 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 700;
  color: #0369a1;
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

.input-panel,
.form-panel {
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
  background: linear-gradient(135deg, #eef9ff, #fff6ea);
}

.example-label {
  font-size: 12px;
  font-weight: 700;
  color: #0369a1;
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

.panel-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 700;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
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

.preview-summary {
  margin-bottom: 18px;
  padding: 14px 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(249, 115, 22, 0.08));
  border: 1px solid rgba(37, 99, 235, 0.08);
}

.preview-title {
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preview-text {
  margin-top: 10px;
  font-size: 13px;
  line-height: 1.7;
  color: #475569;
}

.publish-form {
  max-width: 760px;
}

.field-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #64748b;
}

.upload-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.image-preview-container {
  position: relative;
  width: 156px;
  height: 156px;
  overflow: hidden;
  border: 2px solid #dbe4f0;
  border-radius: 14px;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 12px;
}

.image-actions {
  position: absolute;
  inset: auto 0 0 0;
  display: flex;
  justify-content: center;
  gap: 10px;
  padding: 10px 0;
  background: rgba(15, 23, 42, 0.62);
  opacity: 0;
  transition: opacity 0.25s ease;
}

.image-preview-container:hover .image-actions {
  opacity: 1;
}

.keyword-editor {
  width: 100%;
}

.keyword-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 48px;
  padding: 12px;
  border: 1px solid #dbe4f0;
  border-radius: 14px;
  background: linear-gradient(135deg, #f8fbff, #fffdf8);
}

.keyword-placeholder {
  font-size: 13px;
  color: #94a3b8;
}

.keyword-input-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  margin-top: 10px;
}

.cropper-wrapper {
  width: 100%;
  height: 420px;
  overflow: hidden;
  border-radius: 14px;
  background: #f8fafc;
}

.cropper-image {
  display: block;
  max-width: 100%;
  max-height: 100%;
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










