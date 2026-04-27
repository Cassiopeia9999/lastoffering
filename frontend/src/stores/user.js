import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { apiGetMe, apiLogin } from '@/api'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.is_admin === true)
  const isSuperadmin = computed(() => userInfo.value?.is_superadmin === true)
  const username = computed(() => userInfo.value?.username || '')
  const roleLabel = computed(() => {
    if (isSuperadmin.value) return '超级管理员'
    if (isAdmin.value) return '管理员'
    return '普通用户'
  })

  async function login(username, password) {
    const res = await apiLogin({ username, password })
    token.value = res.access_token
    localStorage.setItem('token', res.access_token)
    await fetchMe()
  }

  async function fetchMe() {
    const res = await apiGetMe()
    userInfo.value = res
    localStorage.setItem('user', JSON.stringify(res))
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isAdmin,
    isSuperadmin,
    username,
    roleLabel,
    login,
    fetchMe,
    logout,
  }
})
