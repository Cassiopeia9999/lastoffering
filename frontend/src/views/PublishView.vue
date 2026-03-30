<template>
  <div class="publish-wrap">
    <el-card shadow="never">
      <template #header>
        <span style="font-size:16px;font-weight:600">
          {{ isEdit ? '编辑物品信息' : '发布失物/招领信息' }}
        </span>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" style="max-width:600px">
        <el-form-item label="信息类型" prop="type">
          <el-radio-group v-model="form.type" size="large">
            <el-radio-button value="lost">
              <el-icon><Warning /></el-icon> 我丢失了
            </el-radio-button>
            <el-radio-button value="found">
              <el-icon><Star /></el-icon> 我捡到了
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="物品图片">
          <div class="upload-area">
            <!-- 图片预览区域 -->
            <div v-if="imagePreview" class="image-preview-container">
              <el-image 
                :src="imagePreview" 
                :preview-src-list="[imagePreview]"
                fit="cover"
                style="width: 100%; height: 100%;"
              />
              <div class="image-actions">
                <el-button circle size="small" type="danger" @click="handleImageRemove" title="删除">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <!-- 上传按钮 -->
            <el-upload v-else ref="uploadRef" :auto-upload="false" :limit="1" accept="image/*"
                       list-type="picture-card" :on-change="handleImageChange" :show-file-list="false">
              <el-icon><Plus /></el-icon>
            </el-upload>
            <div v-if="aiClassifying" class="ai-hint ai-loading">
              <el-icon class="is-loading"><Loading /></el-icon>
              正在识别图片类别，请稍候...
            </div>
            <div v-else-if="aiCategory" class="ai-hint">
              <el-icon color="#67c23a"><MagicStick /></el-icon>
              AI 识别类别：<b>{{ aiCategory }}</b>（置信度 {{ (aiConf * 100).toFixed(0) }}%）
              <el-button link size="small" type="primary" @click="reclassifyImage" style="margin-left: 8px;">
                重新识别
              </el-button>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="物品名称" prop="title">
          <el-input v-model="form.title" placeholder="简短描述物品，如：黑色钱包" clearable />
        </el-form-item>

        <el-form-item label="物品类别" prop="category">
          <el-select v-model="form.category" placeholder="选择类别（可留空由AI识别）" clearable style="width:100%">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
          <div style="font-size:12px;color:#909399;margin-top:4px">
            上传图片后 AI 会自动识别，你也可以手动修改
          </div>
        </el-form-item>

        <el-form-item label="详细描述">
          <el-input v-model="form.description" type="textarea" :rows="3"
                    placeholder="描述物品特征、颜色、品牌等，有助于快速认领" />
          <div style="margin-top: 8px;">
            <el-button type="success" size="small" :loading="aiWriting" :disabled="!imageFile && !form.title"
                       @click="handleAIWrite">
              <el-icon><MagicStick /></el-icon>
              {{ aiWriting ? 'AI生成中...' : 'AI帮写' }}
            </el-button>
            <span style="font-size: 12px; color: #909399; margin-left: 8px;">
              根据图片和物品信息自动生成描述
            </span>
          </div>
        </el-form-item>

        <el-form-item label="地点">
          <el-input v-model="form.location" placeholder="如：图书馆二楼、食堂门口" clearable />
        </el-form-item>

        <el-form-item label="时间">
          <el-date-picker v-model="form.happen_time" type="datetime"
                          placeholder="选择时间" style="width:100%" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" @click="handleSubmit">
            {{ isEdit ? '保存修改' : '发布信息' }}
          </el-button>
          <el-button size="large" @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 图片裁剪对话框 -->
    <el-dialog v-model="showCropper" title="裁剪图片" width="700px" :close-on-click-modal="false" :show-close="false">
      <div class="cropper-wrapper" v-if="cropImageSrc">
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
import { ref, reactive, onMounted, computed, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiCreateItem, apiUpdateItem, apiGetItem, apiGetCategories, apiClassifyImage, apiGenerateDescription } from '@/api'
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'

const router = useRouter()
const route = useRoute()
const formRef = ref()
const loading = ref(false)
const categories = ref([])
const imageFile = ref(null)
const imagePreview = ref('')
const aiCategory = ref('')
const aiConf = ref(0)
const aiWriting = ref(false)
const aiClassifying = ref(false)
const aiTop3 = ref([])  // 保存Top3识别结果
const aiTop3Index = ref(0)  // 当前使用的候选索引

// 裁剪相关
const showCropper = ref(false)
const cropImageSrc = ref('')
const cropFileName = ref('')
const pendingFile = ref(null)
const cropperImg = ref(null)
let cropper = null

// 初始化裁剪器
function initCropper() {
  if (cropper) {
    cropper.destroy()
    cropper = null
  }
  if (cropperImg.value && cropImageSrc.value) {
    // 等图片加载完成后再初始化
    if (cropperImg.value.complete) {
      cropper = new Cropper(cropperImg.value, {
        viewMode: 1,
        autoCropArea: 0.8,
        responsive: true,
      })
    } else {
      cropperImg.value.onload = () => {
        cropper = new Cropper(cropperImg.value, {
          viewMode: 1,
          autoCropArea: 0.8,
          responsive: true,
        })
      }
    }
  }
}

// 监听裁剪对话框显示，初始化裁剪器
watch(showCropper, (val) => {
  if (val && cropImageSrc.value) {
    nextTick(() => {
      initCropper()
    })
  }
})

const isEdit = computed(() => !!route.query.edit)

const form = reactive({
  type: 'lost',
  title: '',
  category: '',
  description: '',
  location: '',
  happen_time: null,
})

const rules = {
  type: [{ required: true }],
  title: [{ required: true, message: '请填写物品名称', trigger: 'blur' }],
}

async function handleImageChange(file) {
  // 生成预览图并打开裁剪对话框
  const reader = new FileReader()
  reader.onload = (e) => {
    cropImageSrc.value = e.target.result
    cropFileName.value = file.raw.name
    showCropper.value = true
    // 保存原始文件，如果用户跳过裁剪会使用
    pendingFile.value = file.raw
  }
  reader.readAsDataURL(file.raw)
}

// 确认裁剪
function confirmCrop() {
  if (!cropper) return
  
  cropper.getCroppedCanvas({
    width: 224,
    height: 224,
    fillColor: '#fff',
    imageSmoothingEnabled: true,
    imageSmoothingQuality: 'high',
  }).toBlob((blob) => {
    // 将裁剪后的图片转为 File 对象
    const croppedFile = new File([blob], cropFileName.value, { type: 'image/jpeg' })
    imageFile.value = croppedFile
    
    // 更新预览图
    const reader = new FileReader()
    reader.onload = (e) => {
      imagePreview.value = e.target.result
    }
    reader.readAsDataURL(blob)
    
    showCropper.value = false
    
    // 调用 AI 识别
    const fd = new FormData()
    fd.append('image', croppedFile)
    aiClassifying.value = true
    aiCategory.value = ''
    apiClassifyImage(fd).then(res => {
      aiTop3.value = res.top3 || []
      aiTop3Index.value = 0
      aiCategory.value = res.suggested_category
      aiConf.value = res.confidence
      if (!form.category) form.category = res.suggested_category
    }).catch(() => {}).finally(() => { aiClassifying.value = false })
  }, 'image/jpeg', 0.9)
}

// 跳过裁剪
function skipCrop() {
  if (!pendingFile.value) return
  
  imageFile.value = pendingFile.value
  imagePreview.value = cropImageSrc.value
  showCropper.value = false
  
  // 调用 AI 识别
  const fd = new FormData()
  fd.append('image', pendingFile.value)
  aiClassifying.value = true
  aiCategory.value = ''
  apiClassifyImage(fd).then(res => {
    aiTop3.value = res.top3 || []
    aiTop3Index.value = 0
    aiCategory.value = res.suggested_category
    aiConf.value = res.confidence
    if (!form.category) form.category = res.suggested_category
  }).catch(() => {}).finally(() => { aiClassifying.value = false })
}

function handleImageRemove() {
  imageFile.value = null
  imagePreview.value = ''
  aiCategory.value = ''
  aiConf.value = 0
  // 如果类别是AI自动识别的，也清空它
  form.category = ''
}

async function reclassifyImage() {
  // 手动重新识别图片类别 - 循环使用Top3候选
  if (!imageFile.value) {
    ElMessage.warning('请先上传图片')
    return
  }
  
  // 如果已经有Top3结果，直接切换到下一个
  if (aiTop3.value.length > 1) {
    aiTop3Index.value = (aiTop3Index.value + 1) % aiTop3.value.length
    const next = aiTop3.value[aiTop3Index.value]
    aiCategory.value = next.category
    aiConf.value = next.confidence
    form.category = next.category
    ElMessage.success(`切换到第${aiTop3Index.value + 1}候选：${next.category}`)
    return
  }
  
  // 否则重新调用API获取Top3
  const fd = new FormData()
  fd.append('image', imageFile.value)
  try {
    const res = await apiClassifyImage(fd)
    aiTop3.value = res.top3 || []
    aiTop3Index.value = 0
    aiCategory.value = res.suggested_category
    aiConf.value = res.confidence
    form.category = res.suggested_category
    ElMessage.success(`识别成功：${res.suggested_category}`)
  } catch (error) {
    ElMessage.error('识别失败，请稍后重试')
    console.error(error)
  }
}

async function handleAIWrite() {
  if (!imageFile.value && !form.title) {
    ElMessage.warning('请至少上传图片或填写物品名称')
    return
  }
  
  aiWriting.value = true
  try {
    const fd = new FormData()
    fd.append('item_type', form.type)
    if (imageFile.value) fd.append('image', imageFile.value)
    if (form.category) fd.append('category', form.category)
    if (form.title) fd.append('title', form.title)
    
    const res = await apiGenerateDescription(fd)
    if (res.success && res.description) {
      form.description = res.description
      ElMessage.success('AI描述生成成功！')
    } else {
      ElMessage.warning(res.message || '生成失败，请手动填写')
    }
  } catch (error) {
    ElMessage.error('AI生成失败，请稍后重试')
    console.error(error)
  } finally {
    aiWriting.value = false
  }
}

async function handleSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    const fd = new FormData()
    fd.append('type', form.type)
    fd.append('title', form.title)
    if (form.category) fd.append('category', form.category)
    if (form.description) fd.append('description', form.description)
    if (form.location) fd.append('location', form.location)
    if (form.happen_time) fd.append('happen_time', new Date(form.happen_time).toISOString())
    if (imageFile.value) fd.append('image', imageFile.value)

    if (isEdit.value) {
      await apiUpdateItem(route.query.edit, {
        title: form.title, category: form.category,
        description: form.description, location: form.location,
      })
      ElMessage.success('修改成功')
    } else {
      const item = await apiCreateItem(fd)
      ElMessage.success('发布成功！')
      router.push(`/items/${item.id}`)
      return
    }
    router.back()
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const catRes = await apiGetCategories()
  categories.value = catRes.categories

  if (isEdit.value) {
    const item = await apiGetItem(route.query.edit)
    Object.assign(form, {
      type: item.type, title: item.title,
      category: item.category || '', description: item.description || '',
      location: item.location || '',
      happen_time: item.happen_time ? new Date(item.happen_time) : null,
    })
  }
})
</script>

<style scoped>
.publish-wrap { max-width: 720px; margin: 0 auto; }
.upload-area { display: flex; flex-direction: column; gap: 8px; }
.ai-loading {
  color: #409eff;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}
.ai-hint {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: #67c23a; padding: 6px 10px;
  background: #f0f9eb; border-radius: 6px;
}

.cropper-wrapper {
  width: 100%;
  height: 400px;
  background: #f5f5f5;
  overflow: hidden;
}

.image-preview-container {
  position: relative;
  width: 148px;
  height: 148px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #dcdfe6;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
}

.preview-image:hover {
  opacity: 0.8;
}

.image-actions {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.3s;
}

.image-preview-container:hover .image-actions {
  opacity: 1;
}
</style>
