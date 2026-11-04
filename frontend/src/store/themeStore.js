import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import i18n from '../i18n'
import { applyPageLanguage } from '../services/pageTranslate'

export const getUiLanguage = (language) => language === 'hi-latn' ? 'en' : language

export const useThemeStore = create(
  persist(
    (set) => ({
      isDark: false,
      language: localStorage.getItem('homecare-lang') || 'en',
      toggleTheme: () => set((s) => ({ isDark: !s.isDark })),
      setLanguage: (lang) => {
        i18n.changeLanguage(getUiLanguage(lang))
        localStorage.setItem('homecare-lang', lang)
        set({ language: lang })
        // translate the WHOLE website, not just the t() strings
        applyPageLanguage(lang)
      },
    }),
    { name: 'homecare-theme' }
  )
)
