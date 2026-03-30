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
            <el-tag v-if="item.status === 'closed'" type="success">已完成</el-tag>
          </div>
          <h2 class="item-title">{{ item.title }}</h2>

          <!-- 发布者信息卡片 -->
          <div class="owner-card" style="margin: 16px 0; padding: 12px; background: #f5f7fa; border-radius: 8px; display: flex; align-items: center; gap: 12px;">
            <el-avatar :size="48" :src="item.owner?.avatar ? 'http://localhost:8000/' + item.owner.avatar : ''" style="background:#409eff">
              {{ (item.owner?.nickname || item.owner?.username || '?').charAt(0).toUpperCase() }}
            </el-avatar>
            <div>
              <div style="font-weight: 600; font-size: 16px;">{{ item.owner?.nickname || item.owner?.username }}</div>
              <div style="font-size: 12px; color: #909399;">发布者</div>
            </div>
          </div>

          <el-descriptions :column="2" border>
            <el-descriptions-item label="物品类别">{{ item.category || '未知' }}</el-descriptions-item>
            <el-descriptions-item label="地点">{{ item.location || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="时间">{{ formatDate(item.happen_time || item.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">{{ item.description || '暂无描述' }}</el-descriptions-item>
          </el-descriptions>

          <!-- 操作按钮 -->
          <div class="action-row" v-if="item.status !== 'closed' && !item.is_deleted">
            <!-- 疑似遗失：只在招领帖子上显示，且不是自己发的 -->
            <template v-if="!isOwner && item.type === 'found'">
              <el-button type="warning" @click="showMatchDialog = true">
                <el-icon><QuestionFilled /></el-icon> 疑似遗失
              </el-button>
            </template>
            <template v-if="isOwner && item.status === 'pending'">
              <el-button @click="router.push(`/publish?edit=${item.id}`)">编辑</el-button>
            </template>
          </div>

          <!-- 待确认匹配：只有招领帖的发布者才能确认/拒绝 -->
          <div class="match-status-card" v-if="matchInfo && matchInfo.status === 'pending' && isOwner && item.type === 'found'">
            <el-alert type="warning" :closable="false" show-icon>
              <template #title>有用户申请匹配此物品，请确认是否同意</template>
            </el-alert>
            <div style="margin-top: 12px; display: flex; gap: 10px;">
              <el-button type="success" @click="handleConfirmMatch">确认匹配</el-button>
              <el-button type="danger" plain @click="handleRejectMatch">拒绝匹配</el-button>
            </div>
          </div>

          <!-- 匹配中状态：显示完成认领按钮 -->
          <div class="match-status-card" v-if="item.status === 'matched' && matchInfo && matchInfo.status === 'confirmed'">
            <el-alert type="success" :closable="false" show-icon>
              <template #title>
                <span>已匹配成功！请线下交接物品</span>
              </template>
              <div style="margin-top: 8px;">
                <span v-if="matchInfo.lost_owner_confirmed && matchInfo.found_owner_confirmed">
                  双方已确认完成
                </span>
                <span v-else>
                  <el-tag v-if="matchInfo.lost_owner_confirmed" size="small" type="success" style="margin-right: 8px;">失物主已确认</el-tag>
                  <el-tag v-else size="small" type="info" style="margin-right: 8px;">失物主未确认</el-tag>
                  <el-tag v-if="matchInfo.found_owner_confirmed" size="small" type="success">招领者已确认</el-tag>
                  <el-tag v-else size="small" type="info">招领者未确认</el-tag>
                </span>
              </div>
            </el-alert>
            <el-button 
              v-if="isOwner && !(item.type === 'lost' ? matchInfo.lost_owner_confirmed : matchInfo.found_owner_confirmed)"
              type="success" 
              style="margin-top: 12px;"
              @click="handleCompleteMatch">
              确认完成认领
            </el-button>
          </div>

          <!-- 已完成状态 -->
          <div class="match-status-card" v-if="item.status === 'closed' && matchInfo?.status === 'completed'">
            <el-alert type="success" :closable="false" show-icon>
              <template #title>
                <span>🎉 物品已成功认领完成！</span>
              </template>
            </el-alert>
          </div>
        </el-col>
      </el-row>

      <!-- 留言区 -->
      <el-divider content-position="left">留言区</el-divider>
      <div class="messages">
        <div v-for="msg in messages" :key="msg.id" class="msg-item">
          <el-avatar :size="32" :src="msg.sender?.avatar ? 'http://localhost:8000/' + msg.sender.avatar : ''" style="background:#409eff;flex-shrink:0">
            {{ (msg.sender?.nickname || msg.sender?.username || '?').charAt(0).toUpperCase() }}
          </el-avatar>
          <div class="msg-body">
            <div class="msg-meta">
              <b>{{ msg.sender?.nickname || msg.sender?.username }}</b>
              <span>{{ formatDate(msg.created_at) }}</span>
              <el-button link size="small" type="primary" @click="replyTo(msg)">回复</el-button>
              <el-button v-if="canDelete(msg)" link size="small" type="danger" @click="deleteMsg(msg)">删除</el-button>
            </div>
            <div class="msg-content">{{ msg.content }}</div>
          </div>
        </div>
        <el-empty v-if="!messages.length" description="暂无留言" :image-size="60" />
      </div>

      <div class="msg-input">
        <el-input v-model="msgContent" :placeholder="replyMsg ? `回复 ${replyMsg.sender?.nickname || replyMsg.sender?.username}:` : '写下你的留言...'" :rows="2" type="textarea" />
        <div style="margin-top:8px; display:flex; gap:8px;">
          <el-button v-if="replyMsg" @click="cancelReply">取消回复</el-button>
          <el-button type="primary" :loading="msgLoading" @click="sendMessage">
            {{ replyMsg ? '发送回复' : '发送留言' }}
          </el-button>
        </div>
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
import { apiGetItem, apiGetMessages, apiPostMessage, apiDeleteMessage, apiCreateMatch,
         apiUpdateItemStatus, apiGetMyItems, apiDeleteItem, apiRestoreItem,
         apiGetMatchByItem, apiCompleteMatch, apiConfirmMatch, apiRejectMatch } from '@/api'

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
const replyMsg = ref(null)  // 当前回复的消息
const matchInfo = ref(null)  // 当前物品的匹配信息

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

    // 尝试加载匹配信息（包括 pending/confirmed/completed 三种状态）
    if (userStore.userInfo) {
      try {
        const match = await apiGetMatchByItem(route.params.id)
        matchInfo.value = match
      } catch (e) {
        console.log('获取匹配信息失败', e)
      }
    }
  } finally {
    loading.value = false
  }
}

async function sendMessage() {
  if (!msgContent.value.trim()) return
  msgLoading.value = true
  try {
    // 如果有回复对象，在内容前添加回复标识
    const content = replyMsg.value 
      ? `回复 ${replyMsg.value.sender?.nickname || replyMsg.value.sender?.username}: ${msgContent.value}`
      : msgContent.value
    const msg = await apiPostMessage(route.params.id, content)
    messages.value.push(msg)
    msgContent.value = ''
    replyMsg.value = null
    ElMessage.success('发送成功')
  } finally {
    msgLoading.value = false
  }
}

function replyTo(msg) {
  replyMsg.value = msg
  // 自动滚动到输入框
  document.querySelector('.msg-input')?.scrollIntoView({ behavior: 'smooth' })
}

function cancelReply() {
  replyMsg.value = null
}

// 判断是否可以删除留言（发送者、物品发布者、管理员）
function canDelete(msg) {
  if (!userStore.userInfo) return false
  const isSender = msg.sender_id === userStore.userInfo.id
  const isOwner = item.value?.owner_id === userStore.userInfo.id
  const isAdmin = userStore.userInfo.is_admin
  return isSender || isOwner || isAdmin
}

async function deleteMsg(msg) {
  try {
    await ElMessageBox.confirm('确认删除这条留言？', '提示', { type: 'warning' })
    await apiDeleteMessage(route.params.id, msg.id)
    messages.value = messages.value.filter(m => m.id !== msg.id)
    ElMessage.success('删除成功')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
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

// 完成认领
async function handleCompleteMatch() {
  if (!matchInfo.value) return
  try {
    await ElMessageBox.confirm('确认物品已交接完成？', '完成认领', { type: 'info' })
    const res = await apiCompleteMatch(matchInfo.value.id)
    matchInfo.value = res
    if (res.status === 'completed') {
      item.value.status = 'closed'
      ElMessage.success('认领完成！感谢你的参与！')
    } else {
      ElMessage.success('已确认完成，等待对方确认')
    }
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('操作失败')
  }
}

// 确认匹配
async function handleConfirmMatch() {
  if (!matchInfo.value) return
  try {
    await ElMessageBox.confirm('确认匹配后，双方将收到对方的联系方式通知', '确认匹配', { type: 'success' })
    const res = await apiConfirmMatch(matchInfo.value.id)
    matchInfo.value = res
    item.value.status = 'matched'
    ElMessage.success('匹配已确认！联系方式已通知双方')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('操作失败')
  }
}

// 拒绝匹配
async function handleRejectMatch() {
  if (!matchInfo.value) return
  try {
    await ElMessageBox.confirm('确认拒绝此次匹配申请？', '拒绝匹配', { type: 'warning' })
    await apiRejectMatch(matchInfo.value.id)
    matchInfo.value = null
    ElMessage.success('已拒绝匹配')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('操作失败')
  }
}

async function handleDelete() {
  await ElMessageBox.confirm('确认下架此条信息？下架后其他人将无法查看', '提示', { type: 'warning' })
  await apiDeleteItem(item.value.id)
  item.value.is_deleted = true
  ElMessage.success('已下架')
}

async function handleRestore() {
  try {
    await apiRestoreItem(item.value.id)
    item.value.is_deleted = false
    ElMessage.success('已重新上架')
  } catch (e) {
    ElMessage.error('重新上架失败')
  }
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
.match-status-card { margin-top: 16px; }
.messages { max-height: 320px; overflow-y: auto; padding: 8px 0; }
.msg-item { display: flex; gap: 10px; margin-bottom: 16px; }
.msg-body { flex: 1; }
.msg-meta { display: flex; gap: 10px; align-items: baseline; margin-bottom: 4px; }
.msg-meta b { font-size: 14px; color: #303133; }
.msg-meta span { font-size: 12px; color: #c0c4cc; }
.msg-content { font-size: 14px; color: #606266; background: #f5f7fa; padding: 8px 12px; border-radius: 8px; }
.msg-input { margin-top: 12px; }
</style>
