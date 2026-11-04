import React, { useEffect, lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import { getUiLanguage, useThemeStore } from './store/themeStore'
import i18n from './i18n'
import { initPageTranslation } from './services/pageTranslate'
import MainLayout from './components/layout/MainLayout'
import AuthLayout from './components/layout/AuthLayout'
import LoadingScreen from './components/ui/LoadingScreen'

// Lazy load pages for performance
const Home          = lazy(() => import('./pages/Home'))
const Dashboard     = lazy(() => import('./pages/Dashboard'))
const SymptomChecker = lazy(() => import('./pages/SymptomChecker'))
const Diseases      = lazy(() => import('./pages/Diseases'))
const DiseaseDetail = lazy(() => import('./pages/DiseaseDetail'))
const OrganBrowser  = lazy(() => import('./pages/OrganBrowser'))
const Chat          = lazy(() => import('./pages/Chat'))
const HealthRecords = lazy(() => import('./pages/HealthRecords'))
const Vitals        = lazy(() => import('./pages/Vitals'))
const Hospitals     = lazy(() => import('./pages/Hospitals'))
const Medicines     = lazy(() => import('./pages/Medicines'))
const Insurance     = lazy(() => import('./pages/Insurance'))
const ImageAnalysis = lazy(() => import('./pages/ImageAnalysis'))
const ReportSummarizer = lazy(() => import('./pages/ReportSummarizer'))
const HealthCoach   = lazy(() => import('./pages/HealthCoach'))
const Telemedicine  = lazy(() => import('./pages/Telemedicine'))
const HomeLab       = lazy(() => import('./pages/HomeLab'))
const Settings      = lazy(() => import('./pages/Settings'))
const Login         = lazy(() => import('./pages/auth/Login'))
const Register      = lazy(() => import('./pages/auth/Register'))
const Emergency     = lazy(() => import('./pages/Emergency'))
const HistoryPage   = lazy(() => import('./pages/History'))

// Protected Route wrapper
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

export default function App() {
  const { isDark, language } = useThemeStore()
  const { initializeAuth } = useAuthStore()

  useEffect(() => {
    // Restore Authorization header from persisted token on every page load/reload
    initializeAuth()
    // Hinglish changes AI responses, while keeping app navigation in English.
    const savedLang = localStorage.getItem('homecare-lang') || language || 'en'
    i18n.changeLanguage(getUiLanguage(savedLang))
    // apply saved language to the whole website on every load
    initPageTranslation(savedLang)
  }, [])

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDark])

  return (
    <Suspense fallback={<LoadingScreen />}>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<Home />} />
        <Route element={<AuthLayout />}>
          <Route path="/login"    element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Route>

        {/* Protected app routes */}
        <Route
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard"       element={<Dashboard />} />
          <Route path="/symptom-checker" element={<SymptomChecker />} />
          <Route path="/diseases"        element={<Diseases />} />
          <Route path="/diseases/:id"    element={<DiseaseDetail />} />
          <Route path="/organs"          element={<OrganBrowser />} />
          <Route path="/chat"            element={<Chat />} />
          <Route path="/records"         element={<HealthRecords />} />
          <Route path="/vitals"          element={<Vitals />} />
          <Route path="/hospitals"       element={<Hospitals />} />
          <Route path="/medicines"       element={<Medicines />} />
          <Route path="/insurance"       element={<Insurance />} />
          <Route path="/image-analysis"  element={<ImageAnalysis />} />
          <Route path="/report-summarizer" element={<ReportSummarizer />} />
          <Route path="/health-coach"    element={<HealthCoach />} />
          <Route path="/telemedicine"    element={<Telemedicine />} />
          <Route path="/home-lab"        element={<HomeLab />} />
          <Route path="/settings"        element={<Settings />} />
          <Route path="/emergency"       element={<Emergency />} />
          <Route path="/history"         element={<HistoryPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}
