import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
    roles?: string[]
    menu?: string
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { title: '工作台', menu: 'dashboard' },
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('@/views/PlaceholderView.vue'),
        meta: { title: '用户管理', menu: 'users', roles: ['ADMIN'] },
      },
      {
        path: 'resources',
        name: 'resources',
        component: () => import('@/views/ResourceView.vue'),
        meta: { title: '资源设备', menu: 'resources' },
      },
      {
        path: 'reservations',
        name: 'reservations',
        component: () => import('@/views/ReservationView.vue'),
        meta: { title: '试验预约', menu: 'reservations' },
      },
      {
        path: 'experiments',
        name: 'experiments',
        component: () => import('@/views/ExperimentView.vue'),
        meta: { title: '试验任务', menu: 'experiments' },
      },
      {
        path: 'monitor',
        name: 'monitor',
        component: () => import('@/views/MonitorView.vue'),
        meta: { title: '数字孪生监控', menu: 'monitor' },
      },
      {
        path: 'alarms',
        name: 'alarms',
        component: () => import('@/views/AlarmView.vue'),
        meta: { title: '告警管理', menu: 'alarms' },
      },
      {
        path: 'archive',
        name: 'archive',
        component: () => import('@/views/PlaceholderView.vue'),
        meta: { title: '试验归档', menu: 'archive' },
      },
      {
        path: 'ai-report',
        name: 'ai-report',
        component: () => import('@/views/PlaceholderView.vue'),
        meta: { title: 'AI 分析', menu: 'ai-report' },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, _from, next) => {
  const userStore = useUserStore()
  document.title = `${to.meta.title || '湖海试验场'} - 数字孪生系统`

  if (to.name === 'login') {
    if (userStore.token) {
      next({ name: 'dashboard' })
    } else {
      next()
    }
    return
  }

  if (to.meta.requiresAuth && !userStore.token) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  if (userStore.token && !userStore.user) {
    try {
      await userStore.fetchProfile()
    } catch {
      await userStore.logout()
      next({ name: 'login' })
      return
    }
  }

  const menu = to.meta.menu as string | undefined
  if (menu && userStore.menus.length > 0 && !userStore.hasMenu(menu)) {
    next({ name: 'dashboard' })
    return
  }

  const roles = to.meta.roles as string[] | undefined
  if (roles && !roles.some((r) => userStore.hasRole(r))) {
    next({ name: 'dashboard' })
    return
  }

  next()
})

export default router
