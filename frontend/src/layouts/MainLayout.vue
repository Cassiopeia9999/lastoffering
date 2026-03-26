<template>
  <el-container class="app-wrapper">
    <!-- 顶部导航 -->
    <el-header class="app-header">
      <div class="header-inner">
        <div class="logo" @click="router.push('/')">
          <el-icon size="22"><Search /></el-icon>
          <span>校园失物招领</span>
        </div>

        <el-menu mode="horizontal" :ellipsis="false" :default-active="activeMenu"
                 router background-color="transparent" text-color="#fff"
                 active-text-color="#ffd04b" class="nav-menu">
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/items">物品列表</el-menu-item>
          <el-menu-item index="/search">
            <el-icon><Camera /></el-icon>以图搜物
          </el-menu-item>
          <el-menu-item index="/publish">发布信息</el-menu-item>
          <el-menu-item index="/my">我的发布</el-menu-item>
        </el-menu>

        <div class="header-right">
          <!-- 通知铃铛 -->
          <el-badge :value="unreadCount || ''" :hidden="!unreadCount" class="notif-badge">
            <el-button circle text @click="router.push('/notifications')">
              <el-icon size="20" color="#fff"><Bell /></el-icon>
            </el-button>
          </el-badge>

          <!-- 用户下拉菜单 -->
          <el-dropdown @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32" :src="avatarUrl" style="background:#409eff">
                {{ displayName.charAt(0).toUpperCase() }}
              </el-avatar>
              <span class="username">{{ displayName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item v-if="userStore.isAdmin" command="admin" divided>
                  管理后台
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </el-header>

    <!-- 主内容区 -->
    <el-main class="app-main">
      <router-view />
    </el-main>

    <!-- 页脚 -->
    <el-footer class="app-footer">
      © 2026 校园失物招领智能管理系统
    </el-footer>
  </el-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { apiGetNotifications } from '@/api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const unreadCount = ref(0)

const activeMenu = computed(() => route.path)
const displayName = computed(() => userStore.userInfo?.nickname || userStore.username)
const avatarUrl = computed(() => {
  const av = userStore.userInfo?.avatar
  if (!av) return ''
  return av.startsWith('http') ? av : `http://localhost:8000/${av}`
})

async function loadUnread() {
  // 未登录时不获取通知
  if (!userStore.isLoggedIn) return
  try {
    const res = await apiGetNotifications()
    unreadCount.value = res.unread
  } catch {}
}

function handleCommand(cmd) {
  if (cmd === 'logout') {
    userStore.logout()
    router.push('/login')
  } else if (cmd === 'admin') {
    router.push('/admin')
  } else if (cmd === 'profile') {
    router.push('/profile')
  }
}

onMounted(loadUnread)
</script>

<style scoped>
.app-wrapper { min-height: 100vh; display: flex; flex-direction: column; }

.app-header {
  background: linear-gradient(135deg, #1a6fc4 0%, #2d8cf0 100%);
  padding: 0;
  height: 60px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  position: sticky; top: 0; z-index: 100;
}
.header-inner {
  max-width: 1200px; margin: 0 auto;
  height: 100%; display: flex; align-items: center; gap: 16px;
  padding: 0 20px;
}
.logo {
  display: flex; align-items: center; gap: 8px;
  color: #fff; font-size: 18px; font-weight: 700;
  cursor: pointer; white-space: nowrap;
}
.nav-menu { flex: 1; border-bottom: none; }
:deep(.el-menu--horizontal .el-menu-item) { color: rgba(255,255,255,0.85) !important; }
:deep(.el-menu--horizontal .el-menu-item.is-active) { color: #ffd04b !important; border-bottom-color: #ffd04b !important; }
.header-right { display: flex; align-items: center; gap: 12px; }
.notif-badge :deep(.el-badge__content) { top: 4px; right: 4px; }
.user-info {
  display: flex; align-items: center; gap: 6px;
  cursor: pointer; color: #fff;
}
.username { font-size: 14px; max-width: 80px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.app-main { flex: 1; background: #f5f7fa; padding: 24px 20px; }
.app-footer {
  text-align: center; color: #999; font-size: 13px;
  background: #fff; border-top: 1px solid #eee;
  height: 48px; line-height: 48px;
}
</style>
