<script setup lang="ts">
import { computed, ref, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Bell,
  Box,
  Calendar,
  DataAnalysis,
  Document,
  Fold,
  Expand,
  HomeFilled,
  List,
  Monitor,
  Setting,
  SwitchButton,
  User,
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const collapsed = ref(false)

interface MenuItem {
  index: string
  title: string
  icon: Component
  menu: string
}

const allMenus: MenuItem[] = [
  { index: '/dashboard', title: '工作台', icon: HomeFilled, menu: 'dashboard' },
  { index: '/users', title: '用户管理', icon: User, menu: 'users' },
  { index: '/audit-logs', title: '操作日志', icon: List, menu: 'audit-logs' },
  { index: '/resources', title: '资源设备', icon: Box, menu: 'resources' },
  { index: '/reservations', title: '试验预约', icon: Calendar, menu: 'reservations' },
  { index: '/experiments', title: '试验任务', icon: Document, menu: 'experiments' },
  { index: '/monitor', title: '数字孪生监控', icon: Monitor, menu: 'monitor' },
  { index: '/alarms', title: '告警管理', icon: Bell, menu: 'alarms' },
  { index: '/archive', title: '试验归档', icon: Setting, menu: 'archive' },
  { index: '/ai-report', title: 'AI 分析', icon: DataAnalysis, menu: 'ai-report' },
]

const visibleMenus = computed(() =>
  allMenus.filter((m) => userStore.hasMenu(m.menu)),
)

const activeMenu = computed(() => route.path)

async function handleLogout() {
  await ElMessageBox.confirm('确定退出登录？', '提示', { type: 'warning' })
  await userStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <el-container class="layout-root">
    <el-aside :width="collapsed ? '64px' : '220px'" class="layout-aside">
      <div class="logo">
        <span v-if="!collapsed">湖海试验场</span>
        <span v-else>湖</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        router
        class="side-menu"
        background-color="#dbeafe"
        text-color="#334155"
        active-text-color="#1d4ed8"
      >
        <el-menu-item
          v-for="item in visibleMenus"
          :key="item.index"
          :index="item.index"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="main-wrap" :class="{ collapsed }">
      <el-header class="layout-header">
        <div class="header-left">
          <el-button text @click="collapsed = !collapsed">
            <el-icon :size="20">
              <Expand v-if="collapsed" />
              <Fold v-else />
            </el-icon>
          </el-button>
          <span class="page-title">{{ route.meta.title }}</span>
        </div>
        <div class="header-right">
          <span class="user-name">{{ userStore.user?.realName }}</span>
          <el-tag
            v-for="role in userStore.user?.roles"
            :key="role"
            size="small"
            type="info"
            class="role-tag"
          >
            {{ role }}
          </el-tag>
          <el-button text type="danger" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            退出
          </el-button>
        </div>
      </el-header>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout-root {
  min-height: 100vh;
}

.layout-aside {
  position: fixed;
  left: 0;
  top: 0;
  z-index: 200;
  height: 100vh;
  background: #dbeafe;
  transition: width 0.2s;
  overflow-x: hidden;
  overflow-y: auto;
}

.main-wrap {
  margin-left: 220px;
  width: calc(100% - 220px);
  min-height: 100vh;
  transition: margin-left 0.2s, width 0.2s;
}

.main-wrap.collapsed {
  margin-left: 64px;
  width: calc(100% - 64px);
}

.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1e40af;
  font-weight: 700;
  font-size: 16px;
  border-bottom: 1px solid #bfdbfe;
  background: #dbeafe;
}

.side-menu {
  border-right: none;
}

.layout-aside :deep(.el-menu) {
  background-color: #dbeafe !important;
  border-right: none;
}

.layout-aside :deep(.el-menu-item:hover) {
  background-color: #bfdbfe !important;
}

.layout-aside :deep(.el-menu-item.is-active) {
  background-color: #93c5fd !important;
  color: #1d4ed8 !important;
  font-weight: 600;
}

.layout-header {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e5e7eb;
  background: #fff;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  color: #374151;
  font-size: 14px;
}

.role-tag {
  margin-right: 4px;
}

.layout-main {
  background: #f3f4f6;
  min-height: calc(100vh - 60px);
}
</style>
