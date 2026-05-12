const TOKEN_KEY = 'diskbench_token'
const REFRESH_TOKEN_KEY = 'diskbench_refresh_token'
import request from '@/utils/request'
export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function setRefreshToken(token) {
  localStorage.setItem(REFRESH_TOKEN_KEY, token)
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}
export function login(data) {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

// 添加刷新 token 的 API
export function refreshToken(refreshToken) {
  return request({
    url: '/auth/refresh',
    method: 'post',
    data: { refresh_token: refreshToken }
  })
}