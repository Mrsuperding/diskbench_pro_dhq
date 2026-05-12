import api from './index'

export const authAPI = {
  // 用户登录
  login(data) {
    return api.post('/auth/login', data)
  },
  
  // 用户注册
  register(data) {
    return api.post('/auth/register', data)
  },
  
  // 获取当前用户信息
  getCurrentUser() {
    return api.get('/auth/me')
  },
  
  // 更新当前用户信息
  updateCurrentUser(data) {
    return api.put('/auth/me', data)
  },
  
  // 修改密码
  changePassword(data) {
    return api.post('/auth/change-password', data)
  },
  
  // 用户登出
  logout() {
    return api.post('/auth/logout')
  },
  
  // 刷新令牌
  refreshToken(data) {
    return api.post('/auth/refresh', data)
  },
  
  // 获取用户列表（管理员）
  getUsers(params = {}) {
    return api.get('/auth/users', { params })
  },
  
  // 更新用户角色（管理员）
  updateUserRole(userId, data) {
    return api.put(`/auth/users/${userId}/role`, data)
  },
  
  // 更新用户状态（管理员）
  updateUserStatus(userId, data) {
    return api.put(`/auth/users/${userId}/status`, data)
  }
}