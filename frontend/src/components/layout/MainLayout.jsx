import React, { useState, useRef, useEffect } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard, Activity, Search, BookOpen, FileText,
  MessageSquare, Heart, MapPin, Pill, Shield, Brain,
  Stethoscope, Video, Settings, LogOut, Menu, X,
  AlertTriangle, ChevronRight, ChevronDown, Bell, User, Sun, Moon,
  Cpu, FileImage, Dumbbell, Globe, Check, FlaskConical, History
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { useThemeStore } from '../../store/themeStore'
import { useTranslation } from 'react-i18next'
import { historyService } from '../../services/api'

const LANGUAGES = [
  { code: 'en', native: 'English' },
  { code: 'hi', native: 'हिंदी' },
  { code: 'hi-latn', native: 'Hinglish' },
  { code: 'mr', native: 'मराठी' },
  { code: 'ta', native: 'தமிழ்' },
  { code: 'te', native: 'తెలుగు' },
  { code: 'kn', native: 'ಕನ್ನಡ' },
  { code: 'ml', native: 'മലയാളം' },
  { code: 'gu', native: 'ગુજરાતી' },
  { code: 'bn', native: 'বাংলা' },
  { code: 'pa', native: 'ਪੰਜਾਬੀ' },
  { code: 'ur', native: 'اردو' },
]

export default function MainLayout() {

  const { t } = useTranslation()

  const navGroups = [
    {
      label: t('nav.overview', 'Overview'),
      items: [
        { to: '/dashboard', icon: LayoutDashboard, label: t('nav.dashboard', 'Dashboard') },
        { to: '/vitals', icon: Activity, label: t('nav.vitals', 'Vitals') },
      ],
    },
    {
      label: t('nav.aiTools', 'AI Tools'),
      items: [
        { to: '/symptom-checker', icon: Search, label: t('nav.symptomChecker', 'Symptom Checker') },
        { to: '/chat', icon: MessageSquare, label: t('nav.aiAssistant', 'AI Assistant') },
        { to: '/image-analysis', icon: FileImage, label: t('nav.imageAnalysis', 'Image Analysis') },
        { to: '/report-summarizer', icon: Cpu, label: t('nav.reportSummarizer', 'Report Summarizer') },
        { to: '/health-coach', icon: Dumbbell, label: t('nav.healthCoach', 'Health Coach') },
      ],
    },
    {
      label: t('nav.medicalLibrary', 'Medical Library'),
      items: [
        { to: '/diseases', icon: BookOpen, label: t('nav.diseases', 'Diseases') },
        { to: '/organs', icon: Brain, label: t('nav.organBrowser', 'Organ Browser') },
      ],
    },
    {
      label: t('nav.recordsAndCare', 'Records & Care'),
      items: [
        { to: '/records', icon: FileText, label: t('nav.records', 'Health Records') },
        { to: '/telemedicine', icon: Video, label: t('nav.telemedicine', 'Telemedicine') },
        { to: '/home-lab', icon: FlaskConical, label: t('nav.laboratory', 'Laboratory') },
        { to: '/insurance', icon: Shield, label: t('nav.insurance', 'Insurance') },
      ],
    },
    {
      label: t('nav.findAndOrder', 'Find & Order'),
      items: [
        { to: '/hospitals', icon: MapPin, label: t('nav.hospitals', 'Nearby Hospitals') },
        { to: '/medicines', icon: Pill, label: t('nav.medicines', 'Medicines') },
      ],
    },
  ]

  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  const [langMenuOpen, setLangMenuOpen] = useState(false)
  const langMenuRef = useRef(null)

  const { user, logout } = useAuthStore()
  const { isDark, toggleTheme, language, setLanguage } = useThemeStore()
  const navigate = useNavigate()
  const location = useLocation()

  const currentLang = LANGUAGES.find(l => l.code === language) || LANGUAGES[0]

  const changeLanguage = (code) => {
    setLanguage(code)
    setLangMenuOpen(false)
  }

  useEffect(() => {
    function handleClickOutside(e) {
      if (langMenuRef.current && !langMenuRef.current.contains(e.target)) {
        setLangMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const pageLabels = {
    '/dashboard': 'Opened Dashboard',
    '/vitals': 'Opened Vitals',
    '/symptom-checker': 'Opened Symptom Checker',
    '/chat': 'Opened AI Assistant',
    '/image-analysis': 'Opened Image Analysis',
    '/report-summarizer': 'Opened Report Summarizer',
    '/health-coach': 'Opened Health Coach',
    '/diseases': 'Opened Diseases',
    '/organs': 'Opened Organ Browser',
    '/records': 'Opened Health Records',
    '/telemedicine': 'Opened Telemedicine',
    '/home-lab': 'Opened Laboratory',
    '/insurance': 'Opened Insurance',
    '/hospitals': 'Opened Nearby Hospitals',
    '/medicines': 'Opened Medicines',
    '/settings': 'Opened Settings',
    '/emergency': 'Opened Emergency',
  }

  useEffect(() => {
    const path = location.pathname
    if (path === '/history' || path === '/login' || path === '/register') return
    const title = Object.entries(pageLabels).find(([prefix]) => path === prefix || path.startsWith(`${prefix}/`))?.[1]
    if (!title) return
    historyService.add({ action: 'page_visit', title, route: path }).catch(() => {})
  }, [location.pathname])

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const SidebarContent = () => (
    <div className="flex flex-col h-full">

      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-6 border-b border-slate-200 dark:border-slate-700">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-teal-500 flex items-center justify-center flex-shrink-0 shadow-sm shadow-blue-500/20">
          <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5">
            <path d="M12 3v18M3 12h18" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
          </svg>
        </div>

        {sidebarOpen && (
          <motion.span
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            translate="no" className="text-lg font-bold text-slate-800 dark:text-slate-100 tracking-tight"
          >
            HomeCare<span className="text-blue-600">+</span>
          </motion.span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 no-scrollbar">
        {navGroups.map((group) => (
          <div key={group.label} className="mb-5">
            {sidebarOpen && (
              <p className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider px-4 mb-2">
                {group.label}
              </p>
            )}

            {group.items.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `nav-item ${isActive ? 'active' : ''} ${!sidebarOpen ? 'justify-center' : ''}`
                }
                title={!sidebarOpen ? label : undefined}
                onClick={() => setMobileSidebarOpen(false)}
              >
                <Icon size={18} className="flex-shrink-0" />
                {sidebarOpen && <span>{label}</span>}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Emergency Button */}
      <div className="px-3 pb-3">
        <button
          onClick={() => { navigate('/emergency'); setMobileSidebarOpen(false) }}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors font-medium text-sm ${!sidebarOpen ? 'justify-center' : ''}`}
        >
          <AlertTriangle size={18} className="flex-shrink-0" />
          {sidebarOpen && 'Emergency'}
        </button>
      </div>

      {/* Settings */}
      <div className="border-t border-slate-200 dark:border-slate-700 px-3 py-4 space-y-1">
        <NavLink
          to="/settings"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''} ${!sidebarOpen ? 'justify-center' : ''}`}
          onClick={() => setMobileSidebarOpen(false)}
        >
          <Settings size={18}/>
          {sidebarOpen && 'Settings'}
        </NavLink>

        <button
          onClick={handleLogout}
          className={`nav-item w-full text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 ${!sidebarOpen ? 'justify-center' : ''}`}
        >
          <LogOut size={18}/>
          {sidebarOpen && 'Logout'}
        </button>

        <NavLink
          to="/history"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''} ${!sidebarOpen ? 'justify-center' : ''}`}
          onClick={() => setMobileSidebarOpen(false)}
        >
          <History size={18}/>
          {sidebarOpen && 'History'}
        </NavLink>
      </div>

      {/* User Profile */}
      {sidebarOpen && user && (
        <div className="px-4 pb-4">
          <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-100 dark:bg-slate-800">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-teal-500 flex items-center justify-center text-white text-xs font-bold">
              {user.firstName?.[0]}{user.lastName?.[0]}
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate">
                {user.firstName} {user.lastName}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                {user.email}
              </p>
            </div>
          </div>
        </div>
      )}

    </div>
  )

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-900 overflow-hidden">

      {/* Desktop Sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: sidebarOpen ? 256 : 72 }}
        transition={{ duration: 0.2 }}
        className="hidden lg:flex flex-col bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700"
      >
        <SidebarContent/>
      </motion.aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

        {/* Header */}
        <header className="h-16 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-700 flex items-center justify-between px-4 sm:px-6 sticky top-0 z-30">

          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileSidebarOpen(true)}
              className="lg:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300"
            >
              <Menu size={20}/>
            </button>

            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="hidden lg:flex p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400"
              title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            >
              <ChevronRight size={18} className={`transition-transform duration-200 ${sidebarOpen ? 'rotate-180' : ''}`}/>
            </button>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">

            {/* Language Switcher */}
            <div className="relative" ref={langMenuRef}>
              <button
                onClick={() => setLangMenuOpen(!langMenuOpen)}
                className="flex items-center gap-1.5 px-2.5 sm:px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition-colors"
              >
                <Globe size={16} className="text-blue-600 dark:text-blue-400 flex-shrink-0"/>
                <span className="text-sm font-medium hidden sm:inline">{currentLang.native}</span>
                <ChevronDown size={14} className={`transition-transform duration-150 ${langMenuOpen ? 'rotate-180' : ''}`}/>
              </button>

              <AnimatePresence>
                {langMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -8, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -8, scale: 0.97 }}
                    transition={{ duration: 0.12 }}
                    className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 py-1.5 max-h-80 overflow-y-auto z-50"
                  >
                    {LANGUAGES.map((lang) => (
                      <button
                        key={lang.code}
                        onClick={() => changeLanguage(lang.code)}
                        className={`w-full flex items-center justify-between px-4 py-2 text-sm transition-colors ${
                          lang.code === currentLang.code
                            ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-semibold'
                            : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/50'
                        }`}
                      >
                        <span>{lang.native}</span>
                        {lang.code === currentLang.code && <Check size={14}/>}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition-colors"
              title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDark ? <Sun size={18}/> : <Moon size={18}/>}
            </button>

            {/* Divider */}
            <div className="hidden sm:block w-px h-8 bg-slate-200 dark:bg-slate-700 mx-1"/>

            {/* User Avatar */}
            <button
              onClick={() => navigate('/settings')}
              className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-teal-500 flex items-center justify-center text-white text-xs font-bold shadow-sm hover:shadow-md transition-shadow flex-shrink-0"
              title={user ? `${user.firstName} ${user.lastName}` : 'Profile'}
            >
              {user?.firstName?.[0]}{user?.lastName?.[0]}
            </button>

          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
            <Outlet/>
          </div>
        </main>

      </div>

    </div>
  )
}