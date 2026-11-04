import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Line, Bar } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend, Filler } from 'chart.js'
import { Heart, Activity, Wind, Droplets, Scale, Dumbbell, Plus, TrendingUp, TrendingDown, CheckCircle } from 'lucide-react'
import { healthService } from '../services/api'
import toast from 'react-hot-toast'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend, Filler)

const vitalsConfig = [
  { key: 'heart_rate',     label: 'Heart Rate',     unit: 'bpm',   icon: Heart,     color: '#ef4444', min: 60, max: 100, normal: '60–100' },
  { key: 'systolic_bp',    label: 'Systolic BP',    unit: 'mmHg',  icon: Activity,  color: '#3b82f6', min: 90,  max: 120, normal: '<120' },
  { key: 'diastolic_bp',   label: 'Diastolic BP',   unit: 'mmHg',  icon: Activity,  color: '#6366f1', min: 60,  max: 80,  normal: '<80' },
  { key: 'oxygen_level',   label: 'Oxygen Level',   unit: '%',     icon: Wind,      color: '#14b8a6', min: 95,  max: 100, normal: '95–100' },
  { key: 'blood_sugar',    label: 'Blood Sugar',    unit: 'mg/dL', icon: Droplets,  color: '#f59e0b', min: 70,  max: 100, normal: '70–100' },
  { key: 'bmi',            label: 'BMI',            unit: '',      icon: Scale,     color: '#8b5cf6', min: 18.5,max: 24.9,normal: '18.5–24.9' },
  { key: 'weight',         label: 'Weight',         unit: 'kg',    icon: Scale,     color: '#06b6d4', min: 0,   max: 999, normal: 'Varies' },
  { key: 'steps',          label: 'Steps',          unit: '',      icon: Dumbbell,  color: '#00a878', min: 0,   max: 99999, normal: '8,000–10,000/day' },
]

const weekLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const chartOpts = (color) => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { grid: { display: false }, ticks: { font: { family: 'Poppins', size: 10 } } },
    y: { grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { font: { family: 'Poppins', size: 10 } } },
  },
})

export default function Vitals() {
  const [form, setForm] = useState({
    heart_rate: '', systolic_bp: '', diastolic_bp: '',
    oxygen_level: '', blood_sugar: '', weight: '', bmi: '', steps: '',
  })
  const [saving, setSaving] = useState(false)
  const [activeChart, setActiveChart] = useState('heart_rate')
  const [latestMetrics, setLatestMetrics] = useState({})
  const [history, setHistory] = useState([])

  // Load latest metrics from backend
  const loadMetrics = async () => {
    try {
      const { data } = await healthService.getMetrics()
      setLatestMetrics(data.metrics || {})
    } catch { /* silent */ }
  }

  // Load history for the active chart metric
  const loadHistory = async (metricType) => {
    try {
      const { data } = await healthService.getHistory(metricType)
      setHistory(data.readings || [])
    } catch { setHistory([]) }
  }

  useEffect(() => { loadMetrics() }, [])
  useEffect(() => { loadHistory(activeChart) }, [activeChart])

  const getStatus = (key, value) => {
    const cfg = vitalsConfig.find((v) => v.key === key)
    if (!cfg || !value) return 'unknown'
    const v = parseFloat(value)
    if (v >= cfg.min && v <= cfg.max) return 'normal'
    return v < cfg.min ? 'low' : 'high'
  }

  const statusBadge = (status) => {
    if (status === 'normal') return 'badge-success'
    if (status === 'low') return 'badge-info'
    if (status === 'high') return 'badge-danger'
    return ''
  }

  const handleSave = async () => {
    const payload = Object.entries(form).reduce((acc, [k, v]) => {
      if (v !== '') acc[k] = parseFloat(v)
      return acc
    }, {})
    if (Object.keys(payload).length === 0) { toast.error('Enter at least one vital'); return }
    setSaving(true)
    try {
      await healthService.addMetric(payload)
      toast.success('Vitals saved successfully!')
      setForm({ heart_rate: '', systolic_bp: '', diastolic_bp: '', oxygen_level: '', blood_sugar: '', weight: '', bmi: '', steps: '' })
      await loadMetrics()
      await loadHistory(activeChart)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save vitals.')
    } finally {
      setSaving(false)
    }
  }

  // Build chart data from real history or zeros
  const historyValues = history.length
    ? history.slice(-7).map((r) => r.value)
    : [0, 0, 0, 0, 0, 0, 0]
  const historyLabels = history.length
    ? history.slice(-7).map((r) => new Date(r.recorded_at).toLocaleDateString('en', { weekday: 'short' }))
    : weekLabels

  const activeCfg = vitalsConfig.find((v) => v.key === activeChart)

  const chartData = {
    labels: historyLabels,
    datasets: [{
      label: activeCfg?.label,
      data: historyValues,
      borderColor: activeCfg?.color,
      backgroundColor: activeCfg?.color + '15',
      borderWidth: 2.5,
      pointRadius: 4,
      pointBackgroundColor: activeCfg?.color,
      tension: 0.4,
      fill: true,
    }],
  }

  const stepsData = {
    labels: historyLabels,
    datasets: [{
      label: 'Steps',
      data: historyValues,
      backgroundColor: historyValues.map((v) => v >= 8000 ? '#00a87830' : '#f59e0b30'),
      borderColor: historyValues.map((v) => v >= 8000 ? '#00a878' : '#f59e0b'),
      borderWidth: 2,
      borderRadius: 6,
    }],
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="section-title">Health Vitals</h1>
        <p className="section-subtitle text-sm">Track and monitor your daily health metrics</p>
      </div>

      {/* Log new vitals */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-5">
          <Plus size={18} className="text-blue-600" />
          <h2 className="font-semibold text-slate-800 dark:text-slate-100">Log Today's Vitals</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
          {vitalsConfig.map(({ key, label, unit, normal }) => (
            <div key={key}>
              <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1.5">
                {label} {unit && <span className="text-slate-400">({unit})</span>}
              </label>
              <input
                type="number"
                step="0.1"
                value={form[key]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                placeholder={`Normal: ${normal}`}
                className={`input-field text-sm py-2 ${
                  form[key] && getStatus(key, form[key]) !== 'normal'
                    ? 'border-red-300 focus:ring-red-400'
                    : form[key] ? 'border-green-300' : ''
                }`}
              />
              {form[key] && (
                <span className={`text-xs ${statusBadge(getStatus(key, form[key]))} mt-1 inline-flex`}>
                  {getStatus(key, form[key])}
                </span>
              )}
            </div>
          ))}
        </div>
        <button onClick={handleSave} disabled={saving} className="btn-primary">
          {saving ? 'Saving...' : <><CheckCircle size={16} /> Save Vitals</>}
        </button>
      </div>

      {/* Chart selector */}
      <div className="glass-card p-6">
        <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Weekly Trends</h2>
        <div className="flex flex-wrap gap-2 mb-5">
          {vitalsConfig.map(({ key, label, color }) => (
              <button key={key} onClick={() => setActiveChart(key)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeChart === key
                    ? 'text-white shadow-sm'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                }`}
                style={activeChart === key ? { backgroundColor: color } : {}}
              >
                {label}
              </button>
            ))}
        </div>
        <div className="h-56">
          {activeChart === 'steps'
            ? <Bar data={stepsData} options={chartOpts(activeCfg?.color)} />
            : <Line data={chartData} options={chartOpts(activeCfg?.color)} />
          }
        </div>
      </div>

      {/* Normal ranges reference */}
      <div className="glass-card p-6">
        <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Normal Reference Ranges</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {vitalsConfig.map(({ key, label, unit, normal, color }) => (
            <div key={key} className="p-3 bg-slate-50 dark:bg-slate-800 rounded-xl">
              <div className="w-2 h-2 rounded-full mb-2" style={{ backgroundColor: color }} />
              <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">{label}</p>
              <p className="text-sm font-bold text-slate-800 dark:text-slate-100 mt-1">{normal} <span className="text-xs font-normal text-slate-400">{unit}</span></p>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-400 mt-4">Reference ranges are general guidelines. Individual normal values may vary. Consult your doctor for personalized targets.</p>
      </div>
    </div>
  )
}
