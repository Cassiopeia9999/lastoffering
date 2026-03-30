import request from './request'

// ── 用户 ──────────────────────────────────────────────────
export const apiRegister = (data) => request.post('/users/register', data)
export const apiLogin = (data) => request.post('/users/login', data)
export const apiGetMe = () => request.get('/users/me')
export const apiUpdateMe = (data) => request.put('/users/me', data)
export const apiUploadAvatar = (formData) => request.post('/users/me/avatar', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

// ── 物品 ──────────────────────────────────────────────────
export const apiGetItems = (params) => request.get('/items', { params })
export const apiGetMyItems = () => request.get('/items/my')
export const apiGetItem = (id) => request.get(`/items/${id}`)
export const apiCreateItem = (formData) => request.post('/items', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const apiUpdateItem = (id, data) => request.put(`/items/${id}`, data)
export const apiUpdateItemStatus = (id, status) => request.patch(`/items/${id}/status`, { status })
export const apiDeleteItem = (id) => request.delete(`/items/${id}`)
export const apiRestoreItem = (id) => request.post(`/items/${id}/restore`)
export const apiCloseItem = (id) => request.post(`/items/${id}/close`)
export const apiGetCategories = () => request.get('/items/categories')

// ── 以图搜物 ──────────────────────────────────────────────
export const apiSearchByImage = (formData) => request.post('/search/by-image', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const apiClassifyImage = (formData) => request.post('/search/classify', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

// ── AI帮写 ────────────────────────────────────────────────
export const apiGenerateDescription = (formData) => request.post('/ai/generate-description', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

// ── 匹配 ──────────────────────────────────────────────────
export const apiCreateMatch = (data) => request.post('/matches', data)
export const apiConfirmMatch = (id) => request.patch(`/matches/${id}/confirm`)
export const apiRejectMatch = (id) => request.patch(`/matches/${id}/reject`)
export const apiCompleteMatch = (id) => request.patch(`/matches/${id}/complete`)
export const apiGetMatchByItem = (itemId) => request.get(`/matches/item/${itemId}`)

// ── 通知 ──────────────────────────────────────────────────
export const apiGetNotifications = () => request.get('/notifications')
export const apiMarkRead = (id) => request.patch(`/notifications/${id}/read`)
export const apiMarkAllRead = () => request.patch('/notifications/read-all')

// ── 留言 ──────────────────────────────────────────────────
export const apiGetMessages = (itemId) => request.get(`/items/${itemId}/messages`)
export const apiPostMessage = (itemId, content) => request.post(`/items/${itemId}/messages`, { content })
export const apiDeleteMessage = (itemId, msgId) => request.delete(`/items/${itemId}/messages/${msgId}`)

// ── 管理员 ────────────────────────────────────────────────
export const apiAdminGetUsers = (params) => request.get('/admin/users', { params })
export const apiAdminUpdateUser = (id, data) => request.patch(`/admin/users/${id}`, data)
export const apiAdminDeleteUser = (id) => request.delete(`/admin/users/${id}`)
export const apiAdminGetItems = (params) => request.get('/admin/items', { params })
export const apiAdminDeleteItem = (id) => request.delete(`/admin/items/${id}`)
export const apiAdminRestoreItem = (id) => request.patch(`/admin/items/${id}/restore`)
export const apiAdminUpdateItemStatus = (id, status) => request.patch(`/admin/items/${id}/status`, { status })
export const apiAdminGetStats = () => request.get('/admin/stats')
export const apiAdminGetCategoryStats = () => request.get('/admin/stats/category')
export const apiAdminGetDailyStats = () => request.get('/admin/stats/daily')
