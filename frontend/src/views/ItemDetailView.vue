<template>
  <div v-loading="loading" class="detail-wrap">
    <template v-if="item">
      <el-page-header @back="router.back()" :content="item.title" />

      <el-row :gutter="24" style="margin-top:20px">
        <!-- 左侧图片 -->
        <el-col :span="8">
          <el-image v-if="item.image_url" :src="`/${item.image_url}`"
                    fit="contain" style="width:100%;border-radius:12px;max-height:320px" />
          <div v-else class="no-img"><el-icon size="60"><Picture /></el-icon><p>暂无图片</p></div>
        </el-col>

        <!-- 右侧信息 -->
        <el-col :span="16">
          <div class="info-header">
            <el-tag :type="item.type === 'lost' ? 'danger' : 'success'" size="large">
              {{ item.type === 'lost' ? '失物' : '招领' }}
            </el-tag>
            <el-tag v-if="item.status === 'matched'" type="info">已匹配</el-tag>
            <el-tag v-if="item.status === 'closed'" type="warning">已关闭</el-tag>
          </div>
          <h2 class="item-title">{{ item.title }}</h2>

          <el-descriptions :column="2" border style="margin-top:16px">
            <el-descriptions-item label="物品类别">{{ item.category || '未知' }}</el-descriptions-item>
            <el-descriptions-item label="发布者">{{ item.owner?.username }}</el-descriptions-item>
            <el-descriptions-item label="地点">{{ item.location || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="时间">{{ formatDate(item.happen_time || item.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">{{ item.description || '暂无描述' }}</el-descriptions-item>
          </el-descriptions>

          <!-- 操作按钮 -->
          <div class="action-row" v-if="item.status === 'pending'">
            <template v-if="!isOwner">
              <el-button type="warning" @click="showMatchDialog = true">
                <el-icon><QuestionFilled /></el-icon> 疑似遗失
              </el-button>
            </template>
            <template v-if="isOwner">
              <el-button @click="router.push(`/publish?edit=${item.id}`)">编辑</el-button>
              <el-button type="danger" plain @click="handleClose">关闭信息</el-button>
            </template>
          </div>
        </el-col>
      </el-row>

      <!-- 留言区 -->
      <el-divider content-position="left">留言区</el-divider>
      <div class="messages">
        <div v-for="msg in messages" :key="msg.id" class="msg-item">
          <el-avatar :size="32" style="background:#409eff;flex-shrink:0">
            {{ msg.sender.username.charAt(0).toUpperCase() }}
          </el-avatar>
          <div class="msg-body">
            <div class="msg-meta">
              <b>{{ msg.sender.username }}</b>
              <span>{{ formatDate(msg.created_at) }}</span>
            </div>
            <div class="msg-content">{{ msg.content }}</div>
          </div>
        </div>
        <el-empty v-if="!messages.length" description="暂无留言" :image-size="60" />
      </div>

      <div class="msg-input">
        <el-input v-model="msgContent" placeholder="写下你的留言..." :rows="2" type="textarea" />
        <el-button type="primary" :loading="msgLoading" @click="sendMessage" style="margin-top:8px">
          发送留言
        </el-button>
      </div>
    </template>

    <!-- 疑似遗失对话框 -->
    <el-dialog v-model="showMatchDialog" title="确认疑似遗失" width="400px">
      <p>你确认这条招领信息中的物品可能是你的失物吗？</p>
      <p style="color:#909399;font-size:13px">确认后系统将通知双方，并在双方确认后交换联系方式。</p>
      <el-form label-width="80px" style="margin-top:16px">
        <el-form-item label="我的失物">
          <el-select v-model="selectedLostId" placeholder="选择你的失物信息" style="width:100%">
            <el-option v-for="li in myLostItems" :key="li.id"
                       :label="li.title" :value="li.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showMatchDialog = false">取消</el-button>
        <el-button type="primary" :loading="matchLoading" @click="handleMatch">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { apiGetItem, apiGetMessages, apiPostMessage, apiCreateMatch,
         apiUpdateItemStatus, apiGetMyItems } from '@/api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const item = ref(null)
const messages = ref([])
const loading = ref(false)
const msgContent = ref('')
const msgLoading = ref(false)
const showMatchDialog = ref(false)
const matchLoading = ref(false)
const selectedLostId = ref(null)
const myLostItems = ref([])

const isOwner = computed(() => item.value?.owner_id === userStore.userInfo?.id)

function formatDate(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function loadData() {
  loading.value = true
  try {
    const [itemRes, msgRes] = await Promise.all([
      apiGetItem(route.params.id),
      apiGetMessages(route.params.id),
    ])
    item.value = itemRes
    messages.value = msgRes.messages
  } finally {
    loading.value = false
  }
}

async function sendMessage() {
  if (!msgContent.value.trim()) return
  msgLoading.value = true
  try {
    const msg = await apiPostMessage(route.params.id, msgContent.value)
    messages.value.push(msg)
    msgContent.value = ''
    ElMessage.success('留言成功')
  } finally {
    msgLoading.value = false
  }
}

async function handleMatch() {
  if (!selectedLostId.value) { ElMessage.warning('请选择你的失物信息'); return }
  matchLoading.value = true
  try {
    await apiCreateMatch({ lost_item_id: selectedLostId.value, found_item_id: item.value.id })
    ElMessage.success('已提交疑似遗失申请，等待双方确认')
    showMatchDialog.value = false
  } finally {
    matchLoading.value = false
  }
}

async function handleClose() {
  await ElMessageBox.confirm('确认关闭此条信息？', '提示', { type: 'warning' })
  await apiUpdateItemStatus(item.value.id, 'closed')
  item.value.status = 'closed'
  ElMessage.success('已关闭')
}

onMounted(async () => {
  await loadData()
  if (item.value?.type === 'found') {
    const res = await apiGetMyItems()
    myLostItems.value = res.items.filter(i => i.type === 'lost' && i.status === 'pending')
  }
})
</script>

<style scoped>
.detail-wrap { max-width: 900px; margin: 0 auto; }
.no-img {
  width: 100%; height: 280px; background: #f5f7fa; border-radius: 12px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  color: #c0c4cc;
}
.info-header { display: flex; gap: 8px; margin-bottom: 8px; }
.item-title { font-size: 22px; margin: 0; color: #303133; }
.action-row { margin-top: 20px; display: flex; gap: 10px; }
.messages { max-height: 320px; overflow-y: auto; padding: 8px 0; }
.msg-item { display: flex; gap: 10px; margin-bottom: 16px; }
.msg-body { flex: 1; }
.msg-meta { display: flex; gap: 10px; align-items: baseline; margin-bottom: 4px; }
.msg-meta b { font-size: 14px; color: #303133; }
.msg-meta span { font-size: 12px; color: #c0c4cc; }
.msg-content { font-size: 14px; color: #606266; background: #f5f7fa; padding: 8px 12px; border-radius: 8px; }
.msg-input { margin-top: 12px; }
</style>
