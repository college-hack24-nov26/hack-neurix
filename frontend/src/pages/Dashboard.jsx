import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link, useNavigate } from 'react-router-dom'
import {
  Heart, Activity, Droplets, Wind, Scale, TrendingUp,
  TrendingDown, AlertCircle, CheckCircle, ArrowRight,
  Search, MessageSquare, FileText, MapPin, Bell, Calendar, FlaskConical
} from 'lucide-react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, ArcElement, Tooltip, Legend, Filler
} from 'chart.js'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../store/authStore'
import { healthService, historyService } from '../services/api'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, ArcElement, Tooltip, Legend, Filler)

const quickActions = [
  { to: '/symptom-checker', icon: Search,       label: 'Check Symptoms',   color: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' },
  { to: '/chat',            icon: MessageSquare, label: 'AI Assistant',     color: 'bg-teal-50 dark:bg-teal-900/20 text-teal-600 dark:text-teal-400' },
  { to: '/records',         icon: FileText,      label: 'Health Records',   color: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400' },
  { to: '/hospitals',       icon: MapPin,        label: 'Find Hospital',    color: 'bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400' },
  { to: '/home-lab',        icon: FlaskConical,  label: 'Book Laboratory Test', color: 'bg-cyan-50 dark:bg-cyan-900/20 text-cyan-600 dark:text-cyan-400' },
]

// Vitals loaded from API (see useEffect below)

const lineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
  scales: {
    x: { grid: { display: false }, ticks: { font: { family: 'Poppins', size: 11 } } },
    y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { font: { family: 'Poppins', size: 11 } } },
  },
}

const container = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } }
const item = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0, transition: { duration: 0.4 } } }

export default function Dashboard() {
  const { user } = useAuthStore()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [vitals, setVitals] = useState([])
  const [healthScore, setHealthScore] = useState(null)
  const [heartTrend, setHeartTrend] = useState([])
  const [recentActivity, setRecentActivity] = useState([])
  const [loading, setLoading] = useState(true)

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 17) return 'Good afternoon'
    return 'Good evening'
  }

  // Map metric keys → display config
  const metricDisplay = {
    heart_rate:     { label: 'Heart Rate',     unit: 'bpm',   icon: Heart,     color: 'text-red-500',    bg: 'bg-red-50 dark:bg-red-900/20' },
    systolic_bp:    { label: 'Systolic BP',    unit: 'mmHg',  icon: Activity,  color: 'text-blue-500',   bg: 'bg-blue-50 dark:bg-blue-900/20' },
    diastolic_bp:   { label: 'Diastolic BP',   unit: 'mmHg',  icon: Activity,  color: 'text-indigo-500', bg: 'bg-indigo-50 dark:bg-indigo-900/20' },
    oxygen_level:   { label: 'Oxygen Level',   unit: '%',     icon: Wind,      color: 'text-teal-500',   bg: 'bg-teal-50 dark:bg-teal-900/20' },
    blood_sugar:    { label: 'Blood Sugar',    unit: 'mg/dL', icon: Droplets,  color: 'text-yellow-500', bg: 'bg-yellow-50 dark:bg-yellow-900/20' },
    bmi:            { label: 'BMI',            unit: '',      icon: Scale,     color: 'text-green-500',  bg: 'bg-green-50 dark:bg-green-900/20' },
  }

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const { data } = await healthService.getDashboard()
        // Build vitals array from latest readings
        const built = Object.entries(data.latest_vitals || {}).map(([key, info]) => {
          const cfg = metricDisplay[key] || { label: key, unit: '', icon: Activity, color: 'text-slate-500', bg: 'bg-slate-50' }
          return { label: cfg.label, value: String(info.value), unit: cfg.unit || info.unit, icon: cfg.icon, status: info.status, trend: 'stable', color: cfg.color, bg: cfg.bg }
        })
        setVitals(built.slice(0, 5))
        setHealthScore(data.health_score ?? null)
        setHeartTrend(data.heart_rate_trend || [])
      } catch {
        // On error keep empty state — UI shows "Log Vitals" prompt
      } finally {
        setLoading(false)
      }
    }
    fetchDashboard()
    historyService.getAll().then(({ data }) => setRecentActivity((data.items || []).slice(0, 4))).catch(() => {})
  }, [])

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row md:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
            {greeting()}, {user?.firstName}
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/vitals" className="btn-secondary text-sm px-4 py-2.5">
            <Activity size={16} /> Log Vitals
          </Link>
          <Link to="/symptom-checker" className="btn-primary text-sm px-4 py-2.5">
            <Search size={16} /> Check Symptoms
          </Link>
        </div>
      </motion.div>

      {/* Health Alert Banner */}
      <motion.div
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        className={`flex items-start gap-3 p-4 rounded-xl border ${
          vitals.length === 0
            ? 'bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-700'
            : healthScore >= 70
              ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
              : 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'
        }`}
      >
        <CheckCircle size={18} className="text-slate-500 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            {vitals.length === 0 ? 'Health Status: No readings yet' : `Health Status: ${healthScore >= 70 ? 'Good' : 'Needs attention'}`}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {vitals.length === 0 ? 'Log your vitals to receive a status based on your data.' : 'Status is estimated from the latest available readings.'}
          </p>
        </div>
      </motion.div>

      {/* Quick Actions */}
      <div>
        <h2 className="section-title text-lg mb-4">{t('dashboard.quickActions', 'Quick Actions')}</h2>
        <motion.div variants={container} initial="hidden" animate="show"
          className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {quickActions.map(({ to, icon: Icon, label, color }) => (
            <motion.div key={to} variants={item}>
              <Link to={to}
                className={`flex flex-col items-center gap-3 p-5 rounded-2xl ${color} hover:shadow-md transition-all duration-200 group`}>
                <div className="w-10 h-10 rounded-xl bg-white/60 dark:bg-white/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Icon size={20} />
                </div>
                <span className="text-sm font-semibold text-center">{label}</span>
              </Link>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Vitals Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title text-lg">{t('dashboard.todayVitals', "Today's Vitals")}</h2>
          <Link to="/vitals" className="text-sm text-blue-600 dark:text-blue-400 font-medium hover:underline flex items-center gap-1">
            View all <ArrowRight size={14} />
          </Link>
        </div>
        <motion.div variants={container} initial="hidden" animate="show"
          className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {loading ? (
            Array.from({length: 5}).map((_, i) => (
              <div key={i} className="glass-card p-4 animate-pulse h-28 rounded-2xl" />
            ))
          ) : vitals.length === 0 ? (
            <div className="col-span-full text-center py-8 text-slate-400 text-sm">
              No vitals logged yet. <Link to="/vitals" className="text-blue-600 font-medium">Log your first reading →</Link>
            </div>
          ) : vitals.map(({ label, value, unit, icon: Icon, status, trend, color, bg }) => (
            <motion.div key={label} variants={item}
              className="glass-card p-4 hover:shadow-card-hover transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <div className={`w-9 h-9 rounded-xl ${bg} flex items-center justify-center`}>
                  <Icon size={17} className={color} />
                </div>
                {trend === 'up'     && <TrendingUp   size={14} className="text-green-500" />}
                {trend === 'down'   && <TrendingDown size={14} className="text-blue-500" />}
                {trend === 'stable' && <span className="text-xs text-slate-400">—</span>}
              </div>
              <p className="text-xl font-bold text-slate-800 dark:text-slate-100">
                {value}<span className="text-xs font-normal text-slate-400 ml-1">{unit}</span>
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{label}</p>
              <span className="badge-success text-xs mt-2 inline-flex">{status}</span>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Charts Row */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Heart Rate Chart */}
        <div className="lg:col-span-2 glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-semibold text-slate-800 dark:text-slate-100">Heart Rate — Weekly</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Beats per minute</p>
            </div>
            <span className="badge-success">
              {heartTrend.length ? `Avg ${Math.round(heartTrend.reduce((sum, r) => sum + Number(r.value), 0) / heartTrend.length)} bpm` : 'No data'}
            </span>
          </div>
          <div className="h-52">
            <Line data={{
              labels: heartTrend.length ? heartTrend.map(r => new Date(r.date).toLocaleDateString('en', { weekday: 'short' })) : [],
              datasets: [{
                label: 'Heart Rate',
                data: heartTrend.length ? heartTrend.map(r => r.value) : [],
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239,68,68,0.08)',
                borderWidth: 2,
                pointRadius: 4,
                pointBackgroundColor: '#ef4444',
                tension: 0.4,
                fill: true,
              }],
            }} options={lineOptions} />
          </div>
        </div>

        {/* Health Score */}
        <div className="glass-card p-6">
          <div className="mb-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-100">Health Score</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Overall wellness breakdown</p>
          </div>
          <div className="text-center py-10">
            <p className="text-3xl font-bold text-gradient">{healthScore !== null ? healthScore : '—'}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">out of 100</p>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="font-semibold text-slate-800 dark:text-slate-100">Recent Activity</h3>
          <Link to="/records" className="text-sm text-blue-600 font-medium hover:underline flex items-center gap-1">
            View all <ArrowRight size={14} />
          </Link>
        </div>
        <div className="space-y-4">
          {recentActivity.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-6">No recent activity yet.</p>
          ) : recentActivity.map((entry) => (
            <button key={entry.id} onClick={() => entry.route && navigate(entry.route)}
              className="w-full flex items-center gap-4 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-left">
              <div className="w-10 h-10 rounded-xl text-blue-500 bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center flex-shrink-0">
                <Activity size={17} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">{entry.title}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{entry.route || 'App activity'}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Disclaimer */}
      <p className="text-xs text-center text-slate-400 dark:text-slate-500 px-4">
        HomeCare+ provides health information for educational purposes only. Always consult a qualified healthcare professional for medical advice, diagnosis, or treatment.
      </p>
    </div>
  )
}
