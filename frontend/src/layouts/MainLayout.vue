<template>
  <el-container class="app-wrapper">
    <el-header class="app-header">
      <div class="header-bg"></div>
      <div class="header-inner">
        <div class="logo" @click="router.push('/')">
          <div class="logo-icon">
            <el-icon size="24"><Search /></el-icon>
          </div>
          <div class="logo-text">
            <span class="logo-title">校园失物招领</span>
            <span class="logo-subtitle">智能匹配系统</span>
          </div>
        </div>

        <el-menu
          mode="horizontal"
          :ellipsis="false"
          :default-active="activeMenu"
          router
          background-color="transparent"
          text-color="rgba(255,255,255,0.9)"
          active-text-color="#fff"
          class="nav-menu"
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>首页
          </el-menu-item>
          <el-menu-item index="/items">
            <el-icon><List /></el-icon>物品列表
          </el-menu-item>
          <el-menu-item index="/search">
            <el-icon><Camera /></el-icon>以图搜物
          </el-menu-item>
          <el-menu-item index="/publish">
            <el-icon><EditPen /></el-icon>发布信息
          </el-menu-item>
          <el-menu-item index="/smart-search">
            <el-icon><ChatDotRound /></el-icon>智能寻物
          </el-menu-item>
          <el-menu-item index="/quick-publish">
            <el-icon><MagicStick /></el-icon>快速发布
          </el-menu-item>
          <el-menu-item index="/my">
            <el-icon><User /></el-icon>我的发布
          </el-menu-item>
        </el-menu>

        <div class="header-right">
          <el-badge :value="unreadCount || ''" :hidden="!unreadCount" class="notif-badge">
            <el-button circle class="icon-btn" @click="router.push('/notifications')">
              <el-icon size="20"><Bell /></el-icon>
            </el-button>
          </el-badge>

          <el-dropdown @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="36" :src="avatarUrl" class="user-avatar">
                {{ displayName.charAt(0).toUpperCase() }}
              </el-avatar>
              <span class="username">{{ displayName }}</span>
              <el-icon class="arrow-icon"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item v-if="userStore.isAdmin" command="admin" divided>
                  <el-icon><Setting /></el-icon>管理后台
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </el-header>

    <el-main class="app-main">
      <router-view />
    </el-main>

    <el-footer class="app-footer">
      <div class="footer-content">
        <div class="footer-icons">
          <el-icon><Search /></el-icon>
          <el-icon><Camera /></el-icon>
          <el-icon><Bell /></el-icon>
        </div>
        <span>© 2026 校园失物招领智能管理系统</span>
      </div>
    </el-footer>
  </el-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { apiGetNotifications } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const unreadCount = ref(0)

const activeMenu = computed(() => route.path)
const displayName = computed(() => userStore.userInfo?.nickname || userStore.username)
const avatarUrl = computed(() => {
  const avatar = userStore.userInfo?.avatar
  if (!avatar) return ''
  return avatar.startsWith('http') ? avatar : `http://localhost:8000/${avatar}`
})

async function loadUnread() {
  if (!userStore.isLoggedIn) return
  try {
    const res = await apiGetNotifications()
    unreadCount.value = res.unread
  } catch {}
}

function handleCommand(command) {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  } else if (command === 'admin') {
    router.push('/admin')
  } else if (command === 'profile') {
    router.push('/profile')
  }
}

onMounted(loadUnread)
</script>

<style scoped>
.app-wrapper { min-height: 100vh; display: flex; flex-direction: column; }

.app-header {
  padding: 0;
  height: 70px;
  position: sticky;
  top: 0;
  z-index: 100;
  background: transparent;
}

.header-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  z-index: -1;
}

.header-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.1) 0%, transparent 100%);
}

.header-inner {
  max-width: 1320px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 0 24px;
  position: relative;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  white-space: nowrap;
}

.logo-icon {
  width: 44px;
  height: 44px;
  background: rgba(255,255,255,0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.logo:hover .logo-icon {
  background: rgba(255,255,255,0.3);
  transform: scale(1.05);
}

.logo-icon .el-icon { color: #fff; }
.logo-text { display: flex; flex-direction: column; }

.logo-title {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
}

.logo-subtitle {
  font-size: 11px;
  color: rgba(255,255,255,0.7);
  letter-spacing: 1px;
}

.nav-menu {
  flex: 1;
  border-bottom: none !important;
  background: transparent !important;
}

:deep(.el-menu--horizontal > .el-menu-item) {
  color: rgba(255,255,255,0.85) !important;
  border-bottom: 2px solid transparent !important;
  padding: 0 14px;
  height: 70px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s ease;
}

:deep(.el-menu--horizontal > .el-menu-item:hover) {
  background: rgba(255,255,255,0.1) !important;
  color: #fff !important;
}

:deep(.el-menu--horizontal > .el-menu-item.is-active) {
  color: #fff !important;
  border-bottom-color: #fff !important;
  background: rgba(255,255,255,0.15) !important;
}

.header-right { display: flex; align-items: center; gap: 16px; }

.icon-btn {
  background: rgba(255,255,255,0.15) !important;
  border: none !important;
  color: #fff !important;
  transition: all 0.3s ease;
}

.icon-btn:hover {
  background: rgba(255,255,255,0.25) !important;
  transform: scale(1.1);
}

.notif-badge :deep(.el-badge__content) {
  top: 4px;
  right: 4px;
  background: #ff6b6b;
  border: none;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: #fff;
  padding: 6px 12px;
  background: rgba(255,255,255,0.1);
  border-radius: 24px;
  transition: all 0.3s ease;
}

.user-info:hover {
  background: rgba(255,255,255,0.2);
}

.user-avatar {
  background: linear-gradient(135deg, #409eff, #66b1ff) !important;
  border: 2px solid rgba(255,255,255,0.3);
}

.username {
  font-size: 14px;
  font-weight: 500;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arrow-icon { transition: transform 0.3s ease; }
.user-info:hover .arrow-icon { transform: rotate(180deg); }

.app-main {
  flex: 1;
  background: transparent;
  padding: 28px 24px;
}

.app-footer {
  text-align: center;
  background: linear-gradient(180deg, transparent, #f8fafc);
  border-top: 1px solid rgba(0,0,0,0.05);
  height: auto;
  padding: 20px;
}

.footer-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-size: 13px;
}

.footer-icons {
  display: flex;
  gap: 16px;
  color: #c0c4cc;
}

.footer-icons .el-icon {
  font-size: 18px;
  transition: all 0.3s ease;
}

.footer-icons .el-icon:hover {
  color: #667eea;
  transform: scale(1.2);
}
</style>
