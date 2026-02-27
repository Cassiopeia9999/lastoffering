import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  { path: '/login',    name: 'Login',    component: () => import('@/views/LoginView.vue'),    meta: { guest: true } },
  { path: '/register', name: 'Register', component: () => import('@/views/RegisterView.vue'), meta: { guest: true } },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '',        name: 'Home',    component: () => import('@/views/HomeView.vue') },
      { path: 'items',   name: 'Items',   component: () => import('@/views/ItemListView.vue') },
      { path: 'items/:id', name: 'ItemDetail', component: () => import('@/views/ItemDetailView.vue') },
      { path: 'publish', name: 'Publish', component: () => import('@/views/PublishView.vue') },
      { path: 'search',  name: 'Search',  component: () => import('@/views/SearchView.vue') },
      { path: 'my',      name: 'My',      component: () => import('@/views/MyItemsView.vue') },
      { path: 'notifications', name: 'Notifications', component: () => import('@/views/NotificationsView.vue') },
      { path: 'profile', name: 'Profile', component: () => import('@/views/ProfileView.vue') },
    ]
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '',        name: 'AdminDashboard', component: () => import('@/views/admin/DashboardView.vue') },
      { path: 'users',   name: 'AdminUsers',     component: () => import('@/views/admin/UsersView.vue') },
      { path: 'items',   name: 'AdminItems',     component: () => import('@/views/admin/ItemsView.vue') },
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')

  if (to.meta.requiresAuth && !token) return next('/login')
  if (to.meta.requiresAdmin && !user?.is_admin) return next('/')
  if (to.meta.guest && token) return next('/')
  next()
})

export default router
