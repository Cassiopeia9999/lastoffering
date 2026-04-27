<template>
  <div class="publish-wrap">
    <el-card shadow="never">
      <template #header>
        <span class="card-title">
          {{ isEdit ? '编辑物品信息' : '发布失物/招领信息' }}
        </span>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" class="publish-form">
        <el-form-item label="信息类型" prop="type">
          <el-radio-group v-model="form.type" size="large">
            <el-radio-button value="lost">
              <el-icon><Warning /></el-icon>
              我丢失了
            </el-radio-button>
            <el-radio-button value="found">
              <el-icon><Star /></el-icon>
              我捡到了
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="物品图片">
          <div class="upload-area">
            <div v-if="imagePreview" class="image-preview-container">
              <el-image
                :src="imagePreview"
                :preview-src-list="[imagePreview]"
                fit="cover"
                style="width: 100%; height: 100%;"
              />
              <div class="image-actions">
                <el-button circle size="small" title="重新裁剪" @click="showCropper = true">
                  <el-icon><Crop /></el-icon>
                </el-button>
                <el-button circle size="small" type="danger" title="删除" @click="handleImageRemove">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <el-upload
              v-else
              ref="uploadRef"
              :auto-upload="false"
              :limit="1"
              accept="image/*"
              list-type="picture-card"
              :on-change="handleImageChange"
              :show-file-list="false"
            >
              <el-icon><Plus /></el-icon>
            </el-upload>

            <div v-if="aiClassifying" class="ai-hint ai-loading">
              <el-icon class="is-loading"><Loading /></el-icon>
              正在识别图片类别，请稍候...
            </div>
            <div v-else-if="aiCategory" class="ai-hint">
              <el-icon color="#67c23a"><MagicStick /></el-icon>
              AI 识别类别：<b>{{ aiCategory }}</b>
              <span>置信度 {{ (aiConf * 100).toFixed(0) }}%</span>
              <el-button link size="small" type="primary" @click="reclassifyImage">
                重新识别
              </el-button>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="物品名称" prop="title">
          <el-input v-model="form.title" placeholder="简短描述物品，如：黑色充电宝" clearable />
        </el-form-item>

        <el-form-item label="物品类别" prop="category">
          <el-select v-model="form.category" placeholder="选择类别（可留空由 AI 识别）" clearable style="width: 100%">
            <el-option v-for="category in categories" :key="category" :label="category" :value="category" />
          </el-select>
          <div class="field-hint">
            上传图片后，系统会自动识别类别，你也可以手动调整。
          </div>
        </el-form-item>

        <el-form-item label="颜色">
          <el-input v-model="form.color" placeholder="如：黑色、银色、蓝白相间" clearable />
        </el-form-item>

        <el-form-item label="品牌">
          <el-input v-model="form.brand" placeholder="如：华为、Apple、小米" clearable />
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
              <span v-if="!form.keywords.length" class="keyword-placeholder">还没有关键词，可以手动添加。</span>
            </div>
            <div class="keyword-input-row">
              <el-input
                v-model="keywordInput"
                placeholder="输入关键词后按回车或点击添加"
                @keyup.enter="addKeyword"
              />
              <el-button @click="addKeyword">添加</el-button>
            </div>
          </div>
          <div class="field-hint">
            关键词支持多个，后续会直接用于 AI 助手理解和异步智能匹配。
          </div>
        </el-form-item>

        <el-form-item label="典型特征">
          <el-input
            v-model="form.feature_text"
            type="textarea"
            :rows="3"
            placeholder="概括该物品最容易被识别的典型特征，如：透明壳、右上角有裂痕、挂着校园卡套"
          />
        </el-form-item>

        <el-form-item label="详细描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="补充物品细节、丢失经过、辨认依据等信息"
          />
        </el-form-item>

        <el-form-item label="地点">
          <el-input v-model="form.location" placeholder="如：图书馆二楼、宿舍楼下、食堂门口" clearable />
        </el-form-item>

        <el-form-item label="时间">
          <el-date-picker v-model="form.happen_time" type="datetime" placeholder="选择时间" style="width: 100%" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" @click="handleSubmit">
            {{ isEdit ? '保存修改' : '发布信息' }}
          </el-button>
          <el-button size="large" @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-dialog v-model="showCropper" title="裁剪图片" width="700px" :close-on-click-modal="false" :show-close="false">
      <div v-if="cropImageSrc" class="cropper-wrapper">
        <img ref="cropperImg" :src="cropImageSrc" style="display: block; max-width: 100%; max-height: 100%;" />
      </div>
      <template #footer>
        <el-button @click="showCropper = false; handleImageRemove()">取消</el-button>
        <el-button @click="skipCrop">跳过裁剪</el-button>
        <el-button type="primary" @click="confirmCrop">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Crop } from '@element-plus/icons-vue'
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'

import {
  apiClassifyImage,
  apiCreateItem,
  apiGetCategories,
  apiGetItem,
  apiUpdateItem,
} from '@/api'

const router = useRouter()
const route = useRoute()

const formRef = ref()
const loading = ref(false)
const categories = ref([])
const imageFile = ref(null)
const imagePreview = ref('')
const aiCategory = ref('')
const aiConf = ref(0)
const aiClassifying = ref(false)
const aiTop3 = ref([])
const aiTop3Index = ref(0)

const showCropper = ref(false)
const cropImageSrc = ref('')
const cropFileName = ref('')
const pendingFile = ref(null)
const cropperImg = ref(null)
const keywordInput = ref('')
let cropper = null

const isEdit = computed(() => Boolean(route.query.edit))

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
  type: [{ required: true }],
  title: [{ required: true, message: '请填写物品名称', trigger: 'blur' }],
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
      autoCropArea: 0.8,
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
  }
})

async function classifyCurrentFile(file) {
  const formData = new FormData()
  formData.append('image', file)
  aiClassifying.value = true
  aiCategory.value = ''
  try {
    const res = await apiClassifyImage(formData)
    aiTop3.value = res.top3 || []
    aiTop3Index.value = 0
    aiCategory.value = res.suggested_category
    aiConf.value = res.confidence
    if (!form.category) {
      form.category = res.suggested_category
    }
  } catch (error) {
    console.error(error)
  } finally {
    aiClassifying.value = false
  }
}

async function handleImageChange(file) {
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

    const reader = new FileReader()
    reader.onload = (event) => {
      imagePreview.value = event.target.result
    }
    reader.readAsDataURL(blob)

    showCropper.value = false
    await classifyCurrentFile(croppedFile)
  }, 'image/jpeg', 0.9)
}

async function skipCrop() {
  if (!pendingFile.value) return
  imageFile.value = pendingFile.value
  imagePreview.value = cropImageSrc.value
  showCropper.value = false
  await classifyCurrentFile(pendingFile.value)
}

function handleImageRemove() {
  imageFile.value = null
  imagePreview.value = ''
  aiCategory.value = ''
  aiConf.value = 0
  form.category = ''
}

async function reclassifyImage() {
  if (!imageFile.value) {
    ElMessage.warning('请先上传图片')
    return
  }

  if (aiTop3.value.length > 1) {
    aiTop3Index.value = (aiTop3Index.value + 1) % aiTop3.value.length
    const next = aiTop3.value[aiTop3Index.value]
    aiCategory.value = next.category
    aiConf.value = next.confidence
    form.category = next.category
    ElMessage.success(`已切换到候选类别：${next.category}`)
    return
  }

  await classifyCurrentFile(imageFile.value)
  if (aiCategory.value) {
    ElMessage.success(`识别成功：${aiCategory.value}`)
  }
}

async function handleSubmit() {
  await formRef.value.validate()
  loading.value = true

  try {
    if (isEdit.value) {
      await apiUpdateItem(route.query.edit, {
        title: form.title,
        category: form.category,
        color: form.color || null,
        brand: form.brand || null,
        keywords: form.keywords,
        feature_text: form.feature_text || null,
        description: form.description || null,
        location: form.location || null,
        happen_time: form.happen_time ? new Date(form.happen_time).toISOString() : null,
      })
      ElMessage.success('修改成功')
      router.back()
      return
    }

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
    loading.value = false
  }
}

onMounted(async () => {
  const categoryRes = await apiGetCategories()
  categories.value = categoryRes.categories || []

  if (!isEdit.value) return

  const item = await apiGetItem(route.query.edit)
  Object.assign(form, {
    type: item.type,
    title: item.title,
    category: item.category || '',
    color: item.color || '',
    brand: item.brand || '',
    keywords: item.keywords || [],
    feature_text: item.feature_text || '',
    description: item.description || '',
    location: item.location || '',
    happen_time: item.happen_time ? new Date(item.happen_time) : null,
  })
})
</script>

<style scoped>
.publish-wrap {
  max-width: 760px;
  margin: 0 auto;
  animation: fadeInUp 0.6s ease-out;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

.publish-form {
  max-width: 600px;
}

.upload-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

.field-inline-hint {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}

.ai-loading {
  color: #667eea;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f4ff 0%, #e8ecff 100%);
  border-radius: 10px;
}

.ai-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #67c23a;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f9eb 0%, #e1f3d8 100%);
  border-radius: 10px;
  border: 1px solid #c2e7b0;
}

.cropper-wrapper {
  width: 100%;
  height: 420px;
  background: #f5f5f5;
  overflow: hidden;
  border-radius: 12px;
}

.image-preview-container {
  position: relative;
  width: 156px;
  height: 156px;
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid #e4e7ed;
  transition: all 0.3s ease;
}

.image-preview-container:hover {
  border-color: #667eea;
}

.image-actions {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 44px;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  opacity: 0;
  transition: opacity 0.3s;
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

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

:deep(.el-radio-button__inner) {
  border-radius: 10px !important;
  padding: 12px 24px;
}

:deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 10px !important;
}

:deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 10px !important;
}

:deep(.el-upload--picture-card) {
  border-radius: 12px !important;
  border: 2px dashed #dcdfe6 !important;
  background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%) !important;
  transition: all 0.3s ease !important;
}

:deep(.el-upload--picture-card:hover) {
  border-color: #667eea !important;
  background: linear-gradient(135deg, #f0f4ff 0%, #e8ecff 100%) !important;
}
</style>
