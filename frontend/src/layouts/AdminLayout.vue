<template>
  <el-container class="admin-wrapper">
    <el-aside width="240px" class="admin-aside">
      <div class="aside-logo">
        <div class="logo-mark">
          <el-icon size="20"><Setting /></el-icon>
        </div>
        <div>
          <div class="logo-title">管理后台</div>
          <div class="logo-subtitle">Campus Lost & Found</div>
        </div>
      </div>

      <el-menu router :default-active="route.path" class="admin-menu">
        <el-menu-item index="/admin">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据概览</span>
        </el-menu-item>
        <el-menu-item index="/admin/ai-insights">
          <el-icon><MagicStick /></el-icon>
          <span>AI效果看板</span>
        </el-menu-item>
        <el-menu-item index="/admin/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/items">
          <el-icon><List /></el-icon>
          <span>物品审核</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="admin-header">
        <div>
          <div class="page-title">{{ pageTitle }}</div>
          <div class="page-subtitle">{{ pageSubtitle }}</div>
        </div>

        <div class="header-actions">
          <el-button plain class="front-btn" @click="router.push('/')">
            <el-icon><Back /></el-icon>
            返回前台
          </el-button>

          <el-dropdown @command="handleCommand">
            <div class="admin-user">
              <el-avatar :size="34" class="user-avatar">
                {{ userStore.username.charAt(0).toUpperCase() }}
              </el-avatar>
              <div class="user-meta">
                <div class="user-name">{{ userStore.username }}</div>
                <div class="user-role">{{ userStore.roleLabel }}</div>
              </div>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="front">返回前台</el-dropdown-item>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import {
  ArrowDown,
  Back,
  DataAnalysis,
  List,
  MagicStick,
  Setting,
  User,
} from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'

import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const titleMap = {
  '/admin': '数据概览',
  '/admin/ai-insights': 'AI效果看板',
  '/admin/users': '用户管理',
  '/admin/items': '物品审核',
}

const subtitleMap = {
  '/admin': '查看整体业务运行情况与核心统计数据',
  '/admin/ai-insights': '展示图像分类、特征抽取、以图搜图和语义增强的数据覆盖情况',
  '/admin/users': '统一管理用户状态、权限与安全操作',
  '/admin/items': '审核物品状态、上下架、删除与内容质量',
}

const pageTitle = computed(() => titleMap[route.path] || '管理后台')
const pageSubtitle = computed(() => subtitleMap[route.path] || '管理员工作台')

function handleCommand(command) {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  } else if (command === 'front') {
    router.push('/')
  } else if (command === 'profile') {
    router.push('/profile')
  }
}
</script>

<style scoped>
.admin-wrapper {
  height: 100vh;
}

.admin-aside {
  overflow: hidden;
  border-right: 1px solid rgba(148, 163, 184, 0.14);
  background: linear-gradient(180deg, #0f172a, #162033 48%, #1f2a44);
  box-shadow: 10px 0 30px rgba(15, 23, 42, 0.12);
}

.aside-logo {
  display: flex;
  align-items: center;
  gap: 14px;
  height: 78px;
  padding: 0 22px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  color: #fff;
  border-radius: 14px;
  background: linear-gradient(135deg, #2563eb, #38bdf8);
}

.logo-title {
  color: #fff;
  font-size: 18px;
  font-weight: 700;
}

.logo-subtitle {
  margin-top: 2px;
  color: rgba(255, 255, 255, 0.62);
  font-size: 11px;
  letter-spacing: 0.08em;
}

.admin-menu {
  padding: 16px 12px;
  border-right: none !important;
  background: transparent !important;
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 82px;
  padding: 0 28px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(10px);
}

.page-title {
  color: #0f172a;
  font-size: 20px;
  font-weight: 800;
}

.page-subtitle {
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.front-btn {
  border-radius: 999px;
}

.admin-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  cursor: pointer;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 18px;
  background: #fff;
}

.user-avatar {
  color: #fff;
  background: linear-gradient(135deg, #2563eb, #0f172a) !important;
}

.user-meta {
  line-height: 1.2;
}

.user-name {
  color: #0f172a;
  font-size: 14px;
  font-weight: 700;
}

.user-role {
  color: #64748b;
  font-size: 12px;
}

.admin-main {
  overflow-y: auto;
  padding: 28px;
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.06), transparent 20%),
    linear-gradient(180deg, #f8fbff 0%, #f3f6fb 100%);
}

:deep(.el-menu-item) {
  height: 50px;
  margin: 5px 0;
  border-radius: 14px;
  color: rgba(255, 255, 255, 0.74) !important;
}

:deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08) !important;
}

:deep(.el-menu-item.is-active) {
  color: #fff !important;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.9), rgba(56, 189, 248, 0.72)) !important;
}
</style>
