import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../services/api'
import toast from 'react-hot-toast'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const { data } = await api.post('/auth/login', { email, password })
          set({
            user: data.user,
            token: data.token,
            isAuthenticated: true,
            isLoading: false,
          })
          api.defaults.headers.common['Authorization'] = `Bearer ${data.token}`
          toast.success(`Welcome back, ${data.user.firstName}!`)
          return { success: true }
        } catch (err) {
          set({ isLoading: false })
          const msg = err.response?.data?.detail || err.response?.data?.message || 'Login failed. Please try again.'
          toast.error(msg)
          return { success: false, error: msg }
        }
      },

      register: async (userData) => {
        set({ isLoading: true })
        try {
          const { data } = await api.post('/auth/register', userData)
          set({
            user: data.user,
            token: data.token,
            isAuthenticated: true,
            isLoading: false,
          })
          api.defaults.headers.common['Authorization'] = `Bearer ${data.token}`
          toast.success('Account created successfully!')
          return { success: true }
        } catch (err) {
          set({ isLoading: false })
          const msg = err.response?.data?.detail || err.response?.data?.message || 'Registration failed. Please try again.'
          toast.error(msg)
          return { success: false, error: msg }
        }
      },

      logout: () => {
        set({ user: null, token: null, isAuthenticated: false })
        delete api.defaults.headers.common['Authorization']
        toast.success('Logged out successfully.')
      },

      updateProfile: async (updates) => {
        try {
          const { data } = await api.put('/auth/profile', updates)
          set({ user: data.user })
          toast.success('Profile updated successfully!')
          return { success: true }
        } catch (err) {
          const msg = err.response?.data?.detail || err.response?.data?.message || 'Update failed.'
          toast.error(msg)
          return { success: false, error: msg }
        }
      },

      initializeAuth: () => {
        const { token } = get()
        if (token) {
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`
        }
      },
    }),
    {
      name: 'homecare-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
