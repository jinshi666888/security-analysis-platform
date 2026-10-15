import { defineStore } from 'pinia'
import { ref } from 'vue'
import { loginApi, meApi } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('sap_token') || '')
  const username = ref('')
  const role = ref('')

  async function login(u: string, p: string) {
    const res = await loginApi(u, p)
    token.value = res.access_token
    username.value = res.username
    role.value = res.role
    localStorage.setItem('sap_token', res.access_token)
  }

  async function fetchMe() {
    try {
      const u = await meApi()
      username.value = u.username
      role.value = u.role
    } catch { logout() }
  }

  function logout() {
    token.value = ''; username.value = ''; role.value = ''
    localStorage.removeItem('sap_token')
  }

  return { token, username, role, login, fetchMe, logout }
})
