import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getProfile, login as loginApi, logout as logoutApi, type UserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<UserInfo | null>(null)
  const menus = ref<string[]>([])

  async function login(username: string, password: string) {
    const { data } = await loginApi(username, password)
    token.value = data.data!.token
    user.value = data.data!.user
    localStorage.setItem('token', token.value)
    await fetchProfile()
  }

  async function fetchProfile() {
    const { data } = await getProfile()
    user.value = data.data!.user
    menus.value = data.data!.menus
  }

  async function logout() {
    try {
      await logoutApi()
    } finally {
      token.value = ''
      user.value = null
      menus.value = []
      localStorage.removeItem('token')
    }
  }

  function hasRole(...roles: string[]) {
    return roles.some((r) => user.value?.roles.includes(r))
  }

  function hasMenu(menu: string) {
    return menus.value.includes(menu)
  }

  return { token, user, menus, login, fetchProfile, logout, hasRole, hasMenu }
})
