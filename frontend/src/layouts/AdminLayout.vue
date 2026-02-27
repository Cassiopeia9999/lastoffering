<template>
  <el-container class="admin-wrapper">
    <el-aside width="220px" class="admin-aside">
      <div class="aside-logo">
        <el-icon size="20"><Setting /></el-icon>
        <span>管理后台</span>
      </div>
      <el-menu router :default-active="route.path" background-color="#1e2a3a"
               text-color="#c0ccda" active-text-color="#409eff">
        <el-menu-item index="/admin">
          <el-icon><DataAnalysis /></el-icon><span>数据概览</span>
        </el-menu-item>
        <el-menu-item index="/admin/users">
          <el-icon><User /></el-icon><span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/items">
          <el-icon><List /></el-icon><span>物品审核</span>
        </el-menu-item>
        <el-menu-item index="/" divided>
          <el-icon><Back /></el-icon><span>返回前台</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="admin-header">
        <span class="page-title">{{ pageTitle }}</span>
        <div class="admin-user">
          <el-avatar :size="28" style="background:#409eff">
            {{ userStore.username.charAt(0).toUpperCase() }}
          </el-avatar>
          <span>{{ userStore.username }}</span>
          <el-button link @click="logout">退出</el-button>
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
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const titleMap = { '/admin': '数据概览', '/admin/users': '用户管理', '/admin/items': '物品审核' }
const pageTitle = computed(() => titleMap[route.path] || '管理后台')

function logout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-wrapper { height: 100vh; }
.admin-aside { background: #1e2a3a; overflow: hidden; }
.aside-logo {
  height: 60px; display: flex; align-items: center; gap: 8px;
  padding: 0 20px; color: #fff; font-size: 16px; font-weight: 700;
  border-bottom: 1px solid #2d3f52;
}
.admin-header {
  background: #fff; border-bottom: 1px solid #eee;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; height: 60px;
}
.page-title { font-size: 16px; font-weight: 600; color: #303133; }
.admin-user { display: flex; align-items: center; gap: 8px; color: #606266; font-size: 14px; }
.admin-main { background: #f5f7fa; padding: 24px; overflow-y: auto; }
</style>
