<template>
  <div class="publish-wrap">
    <el-card shadow="never">
      <template #header>
        <span style="font-size:16px;font-weight:600">
          {{ isEdit ? '编辑物品信息' : '发布失物/招领信息' }}
        </span>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" style="max-width:600px">
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
            <el-upload ref="uploadRef" :auto-upload="false" :limit="1" accept="image/*"
                       list-type="picture-card" :on-change="handleImageChange" :on-remove="handleImageRemove">
              <el-icon><Plus /></el-icon>
            </el-upload>
            <div v-if="aiCategory" class="ai-hint">
              <el-icon color="#67c23a"><MagicStick /></el-icon>
              AI 识别类别：<b>{{ aiCategory }}</b>（置信度 {{ (aiConf * 100).toFixed(0) }}%）
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
        </el-form-item>

        <el-form-item label="丢失/发现地点">
          <el-input v-model="form.location" placeholder="如：图书馆二楼、食堂门口" clearable />
        </el-form-item>

        <el-form-item label="丢失/发现时间">
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiCreateItem, apiUpdateItem, apiGetItem, apiGetCategories, apiClassifyImage } from '@/api'

const router = useRouter()
const route = useRoute()
const formRef = ref()
const loading = ref(false)
const categories = ref([])
const imageFile = ref(null)
const aiCategory = ref('')
const aiConf = ref(0)

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
  imageFile.value = file.raw
  // 上传图片后立即调用 AI 识别类别
  const fd = new FormData()
  fd.append('image', file.raw)
  try {
    const res = await apiClassifyImage(fd)
    aiCategory.value = res.suggested_category
    aiConf.value = res.confidence
    if (!form.category) form.category = res.suggested_category
  } catch {}
}

function handleImageRemove() {
  imageFile.value = null
  aiCategory.value = ''
  aiConf.value = 0
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
.ai-hint {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: #67c23a; padding: 6px 10px;
  background: #f0f9eb; border-radius: 6px;
}
</style>
