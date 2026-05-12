<!--
  登录页 · 极简版
  ================
  改动：
  - 删除：动态粒子、网格底纹、渐变背景、动漫风格
  - 保留：纯粹的登录表单 + 左侧品牌区（单色背景）
  - 视觉：对等分栏布局，大屏幕下左侧展示品牌、右侧表单；窄屏自动折叠
-->
<template>
  <div class="login-page">
    <!-- 左侧品牌区（宽屏下才显示）-->
    <div class="brand-panel">
      <div class="brand-header">
        <div class="brand-mark">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
            <path d="M12 8v4l3 3" stroke-linecap="round" />
          </svg>
        </div>
        <span class="brand-name">DiskBench Pro</span>
      </div>

      <div class="brand-hero">
        <h2 class="hero-title">磁盘 IO 性能测试平台</h2>
        <p class="hero-desc">
          统一下发压测任务、实时收集性能数据、长期沉淀测试资产。
          支持定时调度、基准回归、阈值告警、数据导出。
        </p>

        <ul class="feature-list">
          <li><span class="check">✓</span> 跨系统：Linux / macOS / BSD / 容器</li>
          <li><span class="check">✓</span> 基准对比，性能回归一目了然</li>
          <li><span class="check">✓</span> 定时调度 + 告警，无人值守</li>
          <li><span class="check">✓</span> 数据加密存储、审计留痕</li>
        </ul>
      </div>

      <div class="brand-footer">v1.2 · © 2025</div>
    </div>

    <!-- 右侧登录表单 -->
    <div class="form-panel">
      <div class="form-wrap">
        <div class="form-brand-mobile">
          <div class="brand-mark-sm">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
              <path d="M12 8v4l3 3" stroke-linecap="round" />
            </svg>
          </div>
          <span>DiskBench Pro</span>
        </div>

        <h1 class="form-title">登录</h1>
        <p class="form-desc">输入账号信息以继续</p>

        <form class="form-body" @submit.prevent="handleLogin">
          <div class="field">
            <label>用户名</label>
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              size="large"
              autocomplete="username"
              :prefix-icon="User"
            />
          </div>

          <div class="field">
            <label>密码</label>
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              autocomplete="current-password"
              show-password
              :prefix-icon="Lock"
              @keyup.enter="handleLogin"
            />
          </div>

          <div class="field-row">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            <a class="link-muted" href="#" @click.prevent>忘记密码？</a>
          </div>

          <el-button
            type="primary"
            size="large"
            class="submit-btn"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>

          <!-- 演示账号 -->
          <div class="demo-hint">
            <span class="text-muted">演示账号：</span>
            <a href="#" class="link" @click.prevent="fillDemo('admin','admin123')">admin</a>
            <span class="sep">/</span>
            <a href="#" class="link" @click.prevent="fillDemo('demo','demo123')">demo</a>
          </div>
        </form>

        <div class="form-footer">
          还没有账号？
          <router-link to="/register" class="link">立即注册</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@stores/auth'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const rememberMe = ref(false)
const loginForm = reactive({ username: '', password: '' })

const validate = () => {
  if (!loginForm.username.trim()) { ElMessage.warning('请输入用户名'); return false }
  if (!loginForm.password.trim()) { ElMessage.warning('请输入密码');   return false }
  return true
}

const fillDemo = (u, p) => {
  loginForm.username = u
  loginForm.password = p
}

const handleLogin = async () => {
  if (!validate()) return
  loading.value = true
  try {
    await authStore.login(loginForm)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (err) {
    ElMessage.error(err?.response?.data?.message || '登录失败，请检查账号密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ==============================================================
   双栏容器
   ============================================================== */
.login-page {
  display: flex;
  min-height: 100vh;
  background: var(--bg);
}

/* ==============================================================
   左侧：品牌介绍区（仅大屏显示）
   单色底 + 简单排版，不要任何动态动画
   ============================================================== */
.brand-panel {
  flex: 1.1;
  background: linear-gradient(160deg, #1e3a8a 0%, #2563eb 100%);
  color: #fff;
  padding: 48px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 100vh;
}

.brand-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 600;
}
.brand-mark {
  width: 40px; height: 40px;
  background: rgba(255,255,255,.14);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
}

.brand-hero {
  max-width: 480px;
}
.hero-title {
  font-size: 32px;
  font-weight: 600;
  line-height: 1.2;
  margin: 0 0 16px;
  letter-spacing: -0.5px;
}
.hero-desc {
  font-size: 15px;
  line-height: 1.7;
  color: rgba(255,255,255,.78);
  margin: 0 0 28px;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.feature-list li {
  font-size: 14px;
  color: rgba(255,255,255,.88);
}
.check {
  display: inline-block;
  width: 18px; height: 18px;
  margin-right: 8px;
  background: rgba(255,255,255,.18);
  color: #fff;
  border-radius: 50%;
  text-align: center;
  font-size: 12px;
  line-height: 18px;
}

.brand-footer {
  color: rgba(255,255,255,.6);
  font-size: 13px;
}

/* 窄屏时左侧藏起来，表单全宽 */
@media (max-width: 900px) {
  .brand-panel { display: none; }
}

/* ==============================================================
   右侧：登录表单区
   ============================================================== */
.form-panel {
  flex: 1;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
}
.form-wrap {
  width: 100%;
  max-width: 380px;
}

.form-brand-mobile {
  display: none;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 32px;
}
.brand-mark-sm {
  width: 28px; height: 28px;
  background: var(--brand);
  color: #fff;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
}
@media (max-width: 900px) {
  .form-brand-mobile { display: flex; }
}

.form-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 6px;
  color: var(--text);
}
.form-desc {
  font-size: 14px;
  color: var(--text-2);
  margin: 0 0 28px;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field label {
  font-size: 13px;
  color: var(--text-2);
  font-weight: 500;
}
.field-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: -4px;
}

.submit-btn {
  width: 100%;
  margin-top: 8px;
  height: 44px;
  font-size: 15px;
}

.demo-hint {
  text-align: center;
  font-size: 13px;
  margin-top: 4px;
}
.demo-hint .sep { color: var(--border); margin: 0 6px; }

.form-footer {
  margin-top: 32px;
  font-size: 13px;
  color: var(--text-2);
  text-align: center;
}

/* 链接 */
.link { color: var(--brand); text-decoration: none; }
.link:hover { text-decoration: underline; }
.link-muted { color: var(--text-2); font-size: 13px; text-decoration: none; }
.link-muted:hover { color: var(--brand); }

/* ================= 深色模式支持 ================= */
:global(.dark) .brand-panel {
  background: linear-gradient(160deg, #0f1c3a 0%, #1e40af 100%);
}
</style>
