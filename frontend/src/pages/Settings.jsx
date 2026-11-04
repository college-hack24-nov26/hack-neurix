import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { User, Bell, Shield, Globe, Moon, Sun, Save, CheckCircle, Lock, Eye, EyeOff, Cpu, XCircle, ExternalLink } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { useThemeStore } from '../store/themeStore'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import api, { imageAnalysisService } from '../services/api'

const LANGUAGES = [
  { code: 'en', label: 'English',    native: 'English' },
  { code: 'hi', label: 'Hindi',      native: 'हिंदी (Hindi)' },
  { code: 'hi-latn', label: 'Hinglish', native: 'Hindi in English letters' },
  { code: 'mr', label: 'Marathi',    native: 'मराठी (Marathi)' },
  { code: 'ta', label: 'Tamil',      native: 'தமிழ் (Tamil)' },
  { code: 'te', label: 'Telugu',     native: 'తెలుగు (Telugu)' },
  { code: 'kn', label: 'Kannada',    native: 'ಕನ್ನಡ (Kannada)' },
  { code: 'ml', label: 'Malayalam',  native: 'മലയാളം (Malayalam)' },
  { code: 'gu', label: 'Gujarati',   native: 'ગુજરાતી (Gujarati)' },
  { code: 'bn', label: 'Bengali',    native: 'বাংলা (Bengali)' },
  { code: 'pa', label: 'Punjabi',    native: 'ਪੰਜਾਬੀ (Punjabi)' },
  { code: 'ur', label: 'Urdu',       native: 'اردو (Urdu)' },
]

export default function Settings() {
  const { user, updateProfile } = useAuthStore()
  const { isDark, toggleTheme, language, setLanguage } = useThemeStore()
  const { t } = useTranslation()
  const [form, setForm] = useState({
    firstName: user?.firstName || '', lastName: user?.lastName || '',
    email: user?.email || '', phone: user?.phone || '',
  })
  const [pwForm, setPwForm] = useState({ currentPassword: '', newPassword: '', confirmNew: '' })
  const [showPw, setShowPw] = useState(false)
  const [saving, setSaving] = useState(false)
  const [pwSaving, setPwSaving] = useState(false)
  const [notifications, setNotifications] = useState({
    healthReminders: true, medicationAlerts: true, reportReady: true, newsletter: false,
  })
  const [tab, setTab] = useState('profile')
  const [aiStatus, setAiStatus] = useState(null)

  useEffect(() => {
    imageAnalysisService.status()
      .then(({ data }) => setAiStatus(data))
      .catch(() => setAiStatus(null))
    api.get('/auth/preferences/notifications')
      .then(({ data }) => setNotifications({
        healthReminders: data.healthReminders,
        medicationAlerts: data.medicationAlerts,
        reportReady: data.reportReady,
        newsletter: data.newsletter,
      }))
      .catch(() => {})
  }, [])

  const handleSave = async () => {
    setSaving(true)
    await updateProfile(form)
    setSaving(false)
  }

  const changeLanguage = (code) => {
    setLanguage(code)
    // Save language preference to backend
    api.put('/auth/profile', { language: code }).catch(() => {})
    toast.success('Language updated!')
  }

  const handlePasswordChange = async () => {
    if (!pwForm.currentPassword || !pwForm.newPassword) { toast.error('Fill in all fields'); return }
    if (pwForm.newPassword !== pwForm.confirmNew) { toast.error('New passwords do not match'); return }
    if (pwForm.newPassword.length < 8) { toast.error('Password must be at least 8 characters'); return }
    setPwSaving(true)
    try {
      await api.put('/auth/password', { currentPassword: pwForm.currentPassword, newPassword: pwForm.newPassword })
      toast.success('Password changed successfully!')
      setPwForm({ currentPassword: '', newPassword: '', confirmNew: '' })
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Password change failed.')
    } finally { setPwSaving(false) }
  }

  const tabs = [
    { key: 'profile',       label: t('settings.profile'),       icon: User },
    { key: 'notifications', label: t('settings.notifications'),  icon: Bell },
    { key: 'appearance',    label: t('settings.appearance'),     icon: Moon },
    { key: 'language',      label: t('settings.language'),       icon: Globe },
    { key: 'ai-status',     label: 'AI Status',                  icon: Cpu },
    { key: 'security',      label: t('settings.security'),       icon: Shield },
  ]

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{t('settings.title')}</h1>
        <p className="text-slate-500 text-sm mt-1">{t('settings.subtitle')}</p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button key={key} onClick={() => setTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${tab === key ? 'bg-blue-600 text-white' : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'}`}>
            <Icon size={14} /> {label}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {tab === 'profile' && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-5">{t('settings.profile')}</h2>
          <div className="grid grid-cols-2 gap-4 mb-5">
            {[['firstName','First Name'],['lastName','Last Name'],['email','Email'],['phone','Phone']].map(([key, label]) => (
              <div key={key}>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">{label}</label>
                <input value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  className="input-field" type={key === 'email' ? 'email' : 'text'} />
              </div>
            ))}
          </div>
          <button onClick={handleSave} disabled={saving} className="btn-primary">
            {saving ? 'Saving...' : <><Save size={15} /> {t('settings.saveChanges')}</>}
          </button>
        </motion.div>
      )}

      {/* Notifications Tab */}
      {tab === 'notifications' && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-5">{t('settings.notifications')}</h2>
          <div className="space-y-4">
            {[
              ['healthReminders', 'Health Reminders', 'Daily medication and health check reminders'],
              ['medicationAlerts', 'Medication Alerts', 'Alerts for medication timing and refills'],
              ['reportReady',     'Report Ready',     'Notifications when AI analysis is complete'],
              ['newsletter',      'Health Newsletter', 'Weekly health tips and platform updates'],
            ].map(([key, label, desc]) => (
              <div key={key} className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800 rounded-xl">
                <div>
                  <p className="font-medium text-slate-800 dark:text-slate-100 text-sm">{label}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{desc}</p>
                </div>
                <button onClick={() => {
                  const next = { ...notifications, [key]: !notifications[key] }
                  setNotifications(next)
                  api.put('/auth/preferences/notifications', next)
                    .then(() => toast.success('Notification preferences saved'))
                    .catch(() => toast.error('Could not save notification preferences'))
                }}
                  className={`w-11 h-6 rounded-full transition-colors ${notifications[key] ? 'bg-blue-600' : 'bg-slate-300 dark:bg-slate-600'}`}>
                  <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform mx-0.5 ${notifications[key] ? 'translate-x-5' : 'translate-x-0'}`} />
                </button>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Appearance Tab */}
      {tab === 'appearance' && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-5">{t('settings.appearance')}</h2>
          <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800 rounded-xl">
            <div className="flex items-center gap-3">
              {isDark ? <Moon size={20} className="text-blue-400" /> : <Sun size={20} className="text-yellow-500" />}
              <div>
                <p className="font-medium text-slate-800 dark:text-slate-100 text-sm">{t('settings.darkMode')}</p>
                <p className="text-xs text-slate-400">{isDark ? 'Dark mode is on' : 'Light mode is on'}</p>
              </div>
            </div>
            <button onClick={toggleTheme}
              className={`w-11 h-6 rounded-full transition-colors ${isDark ? 'bg-blue-600' : 'bg-slate-300'}`}>
              <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform mx-0.5 ${isDark ? 'translate-x-5' : 'translate-x-0'}`} />
            </button>
          </div>
        </motion.div>
      )}

      {/* Language Tab */}
      {tab === 'language' && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-2">{t('settings.languageSettings')}</h2>
          <p className="text-slate-400 text-xs mb-5">AI Medical Assistant supports all listed languages for multi-language input.</p>
          <div className="space-y-2">
            {LANGUAGES.map(({ code, native }) => (
              <button key={code} onClick={() => changeLanguage(code)}
                className={`w-full flex items-center justify-between px-4 py-3.5 rounded-xl border transition-all text-left ${
                  language === code
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 font-semibold'
                    : 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:border-blue-300'
                }`}>
                <span className="text-sm">{native}</span>
                {language === code && <CheckCircle size={16} className="text-blue-500" />}
              </button>
            ))}
          </div>
        </motion.div>
      )}

      {/* AI Status Tab */}
      {tab === 'ai-status' && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-2">AI Configuration Status</h2>
          <p className="text-slate-400 text-xs mb-5">
            Shows which AI providers are configured in <code className="px-1 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-[11px]">backend/.env</code> and what features they unlock.
          </p>

          {!aiStatus ? (
            <p className="text-sm text-slate-400">Checking status...</p>
          ) : (
            <div className="space-y-4">
              {/* Feature availability */}
              <div className="grid sm:grid-cols-2 gap-3">
                <div className={`p-4 rounded-xl border ${aiStatus.chat_available ? 'border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-900/20' : 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20'}`}>
                  <div className="flex items-center gap-2 mb-1">
                    {aiStatus.chat_available
                      ? <CheckCircle size={16} className="text-emerald-600 dark:text-emerald-400" />
                      : <XCircle size={16} className="text-red-600 dark:text-red-400" />}
                    <span className="text-sm font-semibold text-slate-800 dark:text-slate-100">AI Chat & Symptom Checker</span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {aiStatus.chat_available ? 'Active — real AI responses enabled.' : 'Not configured — add any API key below.'}
                  </p>
                </div>

                <div className={`p-4 rounded-xl border ${aiStatus.vision_available ? 'border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-900/20' : 'border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20'}`}>
                  <div className="flex items-center gap-2 mb-1">
                    {aiStatus.vision_available
                      ? <CheckCircle size={16} className="text-emerald-600 dark:text-emerald-400" />
                      : <XCircle size={16} className="text-amber-600 dark:text-amber-400" />}
                    <span className="text-sm font-semibold text-slate-800 dark:text-slate-100">Image Analysis</span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {aiStatus.vision_available ? 'Active — X-ray, skin & scan analysis enabled.' : 'Needs an Anthropic, OpenAI or Groq key in backend/.env.'}
                  </p>
                </div>
              </div>

              {/* Provider list */}
              <div>
                <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wide">Providers</p>
                <div className="space-y-2">
                  {[
                    { key: 'openai', label: 'OpenAI', note: 'Chat + Vision', url: 'https://platform.openai.com/account/api-keys' },
                    { key: 'anthropic', label: 'Anthropic Claude', note: 'Chat + Vision', url: 'https://console.anthropic.com/account/keys' },
                    { key: 'groq', label: 'Groq', note: 'Chat only (free)', url: 'https://console.groq.com/keys' },
                  ].map(p => (
                    <div key={p.key} className="flex items-center justify-between px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
                      <div className="flex items-center gap-2.5">
                        {aiStatus.providers?.[p.key]
                          ? <CheckCircle size={15} className="text-emerald-500" />
                          : <XCircle size={15} className="text-slate-300 dark:text-slate-600" />}
                        <div>
                          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{p.label}</p>
                          <p className="text-[11px] text-slate-400">{p.note}</p>
                        </div>
                      </div>
                      {!aiStatus.providers?.[p.key] && (
                        <a href={p.url} target="_blank" rel="noreferrer"
                          className="flex items-center gap-1 text-[11px] font-medium text-blue-600 dark:text-blue-400 hover:underline">
                          Get key <ExternalLink size={10} />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <p className="text-xs text-slate-400 leading-relaxed pt-2 border-t border-slate-100 dark:border-slate-700">
                {aiStatus.message}
              </p>
            </div>
          )}
        </motion.div>
      )}

      {/* Security Tab */}
      {tab === 'security' && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-5">{t('settings.security')}</h2>
          <div className="space-y-4">
            {[
              ['currentPassword', 'Current Password'],
              ['newPassword', 'New Password'],
              ['confirmNew', 'Confirm New Password'],
            ].map(([key, label]) => (
              <div key={key}>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">{label}</label>
                <div className="relative">
                  <Lock size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input type={showPw ? 'text' : 'password'}
                    value={pwForm[key]}
                    onChange={(e) => setPwForm({ ...pwForm, [key]: e.target.value })}
                    className="input-field pl-10 pr-10" />
                  {key === 'newPassword' && (
                    <button type="button" onClick={() => setShowPw(!showPw)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400">
                      {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  )}
                </div>
              </div>
            ))}
            <button onClick={handlePasswordChange} disabled={pwSaving} className="btn-primary mt-2">
              {pwSaving ? 'Updating...' : <><Lock size={15} /> Update Password</>}
            </button>
          </div>
        </motion.div>
      )}
    </div>
  )
}
