<template>
  <div v-loading="loading" class="detail-wrap">
    <template v-if="item">
      <el-page-header :content="item.title" @back="router.back()" />

      <el-row :gutter="24" style="margin-top: 20px;">
        <el-col :span="8">
          <el-image
            v-if="item.image_url"
            :src="`/${item.image_url}`"
            fit="contain"
            style="width: 100%; border-radius: 12px; max-height: 320px;"
          />
          <div v-else class="no-img">
            <el-icon size="60"><Picture /></el-icon>
            <p>暂无图片</p>
          </div>
        </el-col>

        <el-col :span="16">
          <div class="info-header">
            <el-tag :type="item.type === 'lost' ? 'danger' : 'success'" size="large">
              {{ item.type === 'lost' ? '失物' : '招领' }}
            </el-tag>
            <el-tag :type="statusMeta.tagType" class="status-tag">
              <el-icon v-if="statusIcon"><component :is="statusIcon" /></el-icon>
              <span>{{ statusMeta.label }}</span>
            </el-tag>
          </div>

          <h2 class="item-title">{{ item.title }}</h2>

          <div class="owner-card">
            <el-avatar
              :size="48"
              :src="item.owner?.avatar ? `http://localhost:8000/${item.owner.avatar}` : ''"
              style="background: #409eff;"
            >
              {{ (item.owner?.nickname || item.owner?.username || '?').charAt(0).toUpperCase() }}
            </el-avatar>
            <div>
              <div class="owner-name">{{ item.owner?.nickname || item.owner?.username }}</div>
              <div class="owner-role">发布者</div>
            </div>
          </div>

          <el-descriptions :column="2" border>
            <el-descriptions-item label="物品类别">{{ item.category || '未知' }}</el-descriptions-item>
            <el-descriptions-item label="地点">{{ item.location || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="颜色">{{ item.color || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="品牌">{{ item.brand || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="时间">
              {{ formatDate(item.happen_time || item.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="关键词">
              <div v-if="item.keywords?.length" class="keyword-list">
                <el-tag v-for="keyword in item.keywords" :key="keyword" size="small" effect="plain">
                  {{ keyword }}
                </el-tag>
              </div>
              <span v-else>未填写</span>
            </el-descriptions-item>
            <el-descriptions-item label="典型特征" :span="2">
              {{ item.feature_text || '暂无典型特征描述' }}
            </el-descriptions-item>
            <el-descriptions-item label="详细描述" :span="2">
              {{ item.description || '暂无描述' }}
            </el-descriptions-item>
          </el-descriptions>

          <div v-if="item.status !== 'closed' && !item.is_deleted" class="action-row">
            <template v-if="!isOwner && item.type === 'found'">
              <el-button type="warning" @click="showMatchDialog = true">
                <el-icon><QuestionFilled /></el-icon>
                疑似遗失
              </el-button>
            </template>
            <template v-if="isOwner && item.status === 'pending'">
              <el-button @click="router.push(`/publish?edit=${item.id}`)">编辑</el-button>
            </template>
          </div>

          <div
            v-if="matchInfo && matchInfo.status === 'pending' && isOwner && item.type === 'found'"
            class="match-status-card"
          >
            <el-alert type="warning" :closable="false" show-icon>
              <template #title>有用户申请匹配此物品，请确认是否同意</template>
            </el-alert>
            <div class="match-actions">
              <el-button type="success" @click="handleConfirmMatch">确认匹配</el-button>
              <el-button type="danger" plain @click="handleRejectMatch">拒绝匹配</el-button>
            </div>
          </div>

          <div
            v-if="item.status === 'matched' && matchInfo && matchInfo.status === 'confirmed'"
            class="match-status-card"
          >
            <el-alert type="success" :closable="false" show-icon>
              <template #title>已匹配成功，请线下交接物品</template>
              <div style="margin-top: 8px;">
                <span v-if="matchInfo.lost_owner_confirmed && matchInfo.found_owner_confirmed">
                  双方已确认完成
                </span>
                <span v-else>
                  <el-tag
                    v-if="matchInfo.lost_owner_confirmed"
                    size="small"
                    type="success"
                    style="margin-right: 8px;"
                  >
                    失主已确认
                  </el-tag>
                  <el-tag v-else size="small" type="info" style="margin-right: 8px;">
                    失主未确认
                  </el-tag>
                  <el-tag v-if="matchInfo.found_owner_confirmed" size="small" type="success">
                    招领者已确认
                  </el-tag>
                  <el-tag v-else size="small" type="info">
                    招领者未确认
                  </el-tag>
                </span>
              </div>
            </el-alert>
            <el-button
              v-if="isOwner && !(item.type === 'lost' ? matchInfo.lost_owner_confirmed : matchInfo.found_owner_confirmed)"
              type="success"
              style="margin-top: 12px;"
              @click="handleCompleteMatch"
            >
              确认完成认领
            </el-button>
          </div>

          <div v-if="item.status === 'closed' && matchInfo?.status === 'completed'" class="match-status-card">
            <el-alert type="success" :closable="false" show-icon>
              <template #title>物品已成功认领完成</template>
            </el-alert>
          </div>
        </el-col>
      </el-row>

      <el-divider content-position="left">
        {{ item.type === 'lost' ? '可能相关的招领信息' : '可能相关的失物信息' }}
      </el-divider>
      <div class="similar-section">
        <div v-if="similarLoading" class="similar-loading">
          <el-skeleton :rows="3" animated />
        </div>
        <div v-else-if="similarItems.length" class="similar-grid">
          <ItemCard v-for="record in similarItems" :key="record.item.id" :item="record.item" />
        </div>
        <el-empty
          v-else
          description="暂未发现高相关物品，后续匹配结果会通过通知推送给你"
          :image-size="64"
        />
      </div>

      <el-divider content-position="left">留言区</el-divider>
      <div class="messages">
        <div v-for="msg in messages" :key="msg.id" class="msg-item">
          <el-avatar
            :size="32"
            :src="msg.sender?.avatar ? `http://localhost:8000/${msg.sender.avatar}` : ''"
            style="background: #409eff; flex-shrink: 0;"
          >
            {{ (msg.sender?.nickname || msg.sender?.username || '?').charAt(0).toUpperCase() }}
          </el-avatar>
          <div class="msg-body">
            <div class="msg-meta">
              <b>{{ msg.sender?.nickname || msg.sender?.username }}</b>
              <span>{{ formatDate(msg.created_at) }}</span>
              <el-button link size="small" type="primary" @click="replyTo(msg)">回复</el-button>
              <el-button v-if="canDelete(msg)" link size="small" type="danger" @click="deleteMsg(msg)">
                删除
              </el-button>
            </div>
            <div class="msg-content">{{ msg.content }}</div>
          </div>
        </div>
        <el-empty v-if="!messages.length" description="暂无留言" :image-size="60" />
      </div>

      <div class="msg-input">
        <el-input
          v-model="msgContent"
          :placeholder="replyMsg ? `回复 ${replyMsg.sender?.nickname || replyMsg.sender?.username}:` : '写下你的留言...'"
          :rows="2"
          type="textarea"
        />
        <div style="margin-top: 8px; display: flex; gap: 8px;">
          <el-button v-if="replyMsg" @click="cancelReply">取消回复</el-button>
          <el-button type="primary" :loading="msgLoading" @click="sendMessage">
            {{ replyMsg ? '发送回复' : '发送留言' }}
          </el-button>
        </div>
      </div>
    </template>

    <el-dialog v-model="showMatchDialog" title="确认疑似遗失" width="400px">
      <p>你确认这条招领信息中的物品可能是你的失物吗？</p>
      <p style="color: #909399; font-size: 13px;">
        确认后系统将通知双方，并在双方确认后交换联系方式。
      </p>
      <el-form label-width="80px" style="margin-top: 16px;">
        <el-form-item label="我的失物">
          <el-select v-model="selectedLostId" placeholder="选择你的失物信息" style="width: 100%">
            <el-option v-for="lostItem in myLostItems" :key="lostItem.id" :label="lostItem.title" :value="lostItem.id" />
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
import { CircleCheck, Clock, Connection, Picture, QuestionFilled } from '@element-plus/icons-vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import ItemCard from '@/components/ItemCard.vue'
import { useUserStore } from '@/stores/user'
import { getItemStatusMeta } from '@/utils/itemStatus'
import {
  apiCompleteMatch,
  apiConfirmMatch,
  apiCreateMatch,
  apiDeleteMessage,
  apiGetItem,
  apiGetMatchByItem,
  apiGetMessages,
  apiGetMyItems,
  apiGetSimilarItems,
  apiPostMessage,
  apiRejectMatch,
} from '@/api'

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
const replyMsg = ref(null)
const matchInfo = ref(null)
const similarItems = ref([])
const similarLoading = ref(false)

const statusIconMap = {
  Clock,
  Connection,
  CircleCheck,
}

const isOwner = computed(() => item.value?.owner_id === userStore.userInfo?.id)
const statusMeta = computed(() => getItemStatusMeta(item.value?.status))
const statusIcon = computed(() => statusIconMap[statusMeta.value.icon] || null)

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function loadData() {
  loading.value = true
  try {
    const [itemRes, messageRes] = await Promise.all([
      apiGetItem(route.params.id),
      apiGetMessages(route.params.id),
    ])

    item.value = itemRes
    messages.value = messageRes.messages

    if (userStore.userInfo) {
      try {
        matchInfo.value = await apiGetMatchByItem(route.params.id)
      } catch (error) {
        console.log('获取匹配信息失败', error)
      }
    }
  } finally {
    loading.value = false
  }
}

async function loadSimilarItems() {
  similarLoading.value = true
  try {
    const res = await apiGetSimilarItems(route.params.id, { limit: 4, threshold: 0.35 })
    similarItems.value = res.items || []
  } catch (error) {
    console.error(error)
    similarItems.value = []
  } finally {
    similarLoading.value = false
  }
}

async function reloadAll() {
  messages.value = []
  similarItems.value = []
  matchInfo.value = null
  replyMsg.value = null
  msgContent.value = ''
  await loadData()
  await loadSimilarItems()
  if (item.value?.type === 'found') {
    const res = await apiGetMyItems()
    myLostItems.value = res.items.filter((record) => record.type === 'lost' && record.status === 'pending')
  } else {
    myLostItems.value = []
  }
}

async function sendMessage() {
  if (!msgContent.value.trim()) return
  msgLoading.value = true
  try {
    const content = replyMsg.value
      ? `回复 ${replyMsg.value.sender?.nickname || replyMsg.value.sender?.username}: ${msgContent.value}`
      : msgContent.value
    const message = await apiPostMessage(route.params.id, content)
    messages.value.push(message)
    msgContent.value = ''
    replyMsg.value = null
    ElMessage.success('发送成功')
  } finally {
    msgLoading.value = false
  }
}

function replyTo(msg) {
  replyMsg.value = msg
  document.querySelector('.msg-input')?.scrollIntoView({ behavior: 'smooth' })
}

function cancelReply() {
  replyMsg.value = null
}

function canDelete(msg) {
  if (!userStore.userInfo) return false
  const isSender = msg.sender_id === userStore.userInfo.id
  const owner = item.value?.owner_id === userStore.userInfo.id
  const isAdmin = userStore.userInfo.is_admin
  return isSender || owner || isAdmin
}

async function deleteMsg(msg) {
  try {
    await ElMessageBox.confirm('确认删除这条留言？', '提示', { type: 'warning' })
    await apiDeleteMessage(route.params.id, msg.id)
    messages.value = messages.value.filter((message) => message.id !== msg.id)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function handleMatch() {
  if (!selectedLostId.value) {
    ElMessage.warning('请选择你的失物信息')
    return
  }
  matchLoading.value = true
  try {
    await apiCreateMatch({ lost_item_id: selectedLostId.value, found_item_id: item.value.id })
    ElMessage.success('已提交疑似遗失申请，等待双方确认')
    showMatchDialog.value = false
  } finally {
    matchLoading.value = false
  }
}

async function handleCompleteMatch() {
  if (!matchInfo.value) return
  try {
    await ElMessageBox.confirm('确认物品已交接完成？', '完成认领', { type: 'info' })
    const res = await apiCompleteMatch(matchInfo.value.id)
    matchInfo.value = res
    if (res.status === 'completed') {
      item.value.status = 'closed'
      ElMessage.success('认领完成')
    } else {
      ElMessage.success('已确认完成，等待对方确认')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

async function handleConfirmMatch() {
  if (!matchInfo.value) return
  try {
    await ElMessageBox.confirm('确认匹配后，双方将收到联系方式通知', '确认匹配', { type: 'success' })
    const res = await apiConfirmMatch(matchInfo.value.id)
    matchInfo.value = res
    item.value.status = 'matched'
    ElMessage.success('匹配已确认')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

async function handleRejectMatch() {
  if (!matchInfo.value) return
  try {
    await ElMessageBox.confirm('确认拒绝此次匹配申请？', '拒绝匹配', { type: 'warning' })
    await apiRejectMatch(matchInfo.value.id)
    matchInfo.value = null
    ElMessage.success('已拒绝匹配')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

onMounted(reloadAll)

watch(() => route.params.id, async (newId, oldId) => {
  if (newId && newId !== oldId) {
    await reloadAll()
  }
})
</script>

<style scoped>
.detail-wrap {
  max-width: 960px;
  margin: 0 auto;
  animation: fadeInUp 0.6s ease-out;
}

.no-img {
  width: 100%;
  height: 320px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
}

.info-header {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.status-tag :deep(.el-icon) {
  margin-right: 4px;
}

.item-title {
  margin: 0;
  font-size: 26px;
  color: #303133;
  font-weight: 700;
}

.owner-card {
  margin: 20px 0;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
  border-radius: 14px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.owner-name {
  font-weight: 600;
  font-size: 16px;
}

.owner-role {
  font-size: 12px;
  color: #909399;
}

.keyword-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.action-row {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}

.match-status-card {
  margin-top: 20px;
  padding: 16px;
  border-radius: 12px;
}

.match-actions {
  margin-top: 12px;
  display: flex;
  gap: 10px;
}

.messages {
  max-height: 420px;
  overflow-y: auto;
  padding: 12px 0;
}

.msg-item {
  display: flex;
  gap: 14px;
  margin-bottom: 20px;
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 16px;
  background: linear-gradient(135deg, #fff, #fbfdff);
  transition: all 0.25s ease;
}

.msg-item:hover {
  border-color: rgba(37, 99, 235, 0.18);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
}

.msg-body {
  flex: 1;
}

.msg-meta {
  display: flex;
  gap: 12px;
  align-items: baseline;
  margin-bottom: 8px;
}

.msg-meta b {
  font-size: 15px;
  color: #303133;
}

.msg-meta span {
  font-size: 13px;
  color: #c0c4cc;
}

.msg-content {
  font-size: 14px;
  color: #334155;
  background: linear-gradient(135deg, #f8fbff 0%, #fffdf8 100%);
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
}

.msg-input {
  margin-top: 16px;
  padding: 16px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 18px;
  background: linear-gradient(135deg, #f8fbff, #fffdf8);
}

.similar-section {
  margin-bottom: 8px;
}

.similar-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.similar-loading {
  padding: 8px 0 20px;
}

:deep(.el-page-header) {
  margin-bottom: 20px;
}

:deep(.el-page-header__back) {
  font-size: 15px;
}

:deep(.el-descriptions) {
  background: #fafbfc;
  border-radius: 14px;
  padding: 4px;
}

:deep(.el-descriptions__label) {
  font-weight: 600;
  color: #606266;
}

:deep(.el-descriptions__content) {
  color: #303133;
}

:deep(.el-image) {
  border-radius: 20px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
}

:deep(.el-divider__text) {
  font-weight: 600;
  color: #606266;
  font-size: 15px;
}

@media (max-width: 768px) {
  .similar-grid {
    grid-template-columns: 1fr;
  }
}
</style>
