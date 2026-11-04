// Emergency.jsx
import React from 'react'
import { motion } from 'framer-motion'
import { Phone, AlertTriangle, Heart, Activity, MapPin, MessageSquare } from 'lucide-react'
import { Link } from 'react-router-dom'

const emergencyNumbers = [
  { label: 'National Emergency',  number: '112', color: 'bg-red-600',    desc: 'Police, Fire, Ambulance' },
  { label: 'Ambulance',           number: '108', color: 'bg-red-500',    desc: 'Medical emergency' },
  { label: 'Police',              number: '100', color: 'bg-blue-600',   desc: 'Law enforcement' },
  { label: 'Women Helpline',      number: '1091', color: 'bg-pink-600',  desc: 'Women in distress' },
  { label: 'Suicide Prevention',  number: 'iCall: 9152987821', color: 'bg-purple-600', desc: 'Mental health crisis' },
  { label: 'Poison Control',      number: '1800-11-6117', color: 'bg-orange-600', desc: 'Poisoning emergencies' },
]

const warningSigns = [
  { sign: 'Chest pain or pressure', action: 'Call 108 immediately — may be a heart attack' },
  { sign: 'Difficulty breathing', action: 'Sit upright, loosen clothing, call 108' },
  { sign: 'Sudden severe headache', action: 'Do not lie down, call 108 — may be a stroke' },
  { sign: 'Loss of consciousness', action: 'Place in recovery position, call 108' },
  { sign: 'Severe allergic reaction', action: 'Use epinephrine if available, call 108' },
  { sign: 'Heavy bleeding', action: 'Apply firm pressure, elevate limb, call 108' },
  { sign: 'Stroke symptoms (FAST)', action: 'Face drooping, Arm weakness, Speech difficulty, Time to call 108' },
]

export default function Emergency() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3 p-5 bg-red-50 dark:bg-red-900/20 rounded-2xl border border-red-200 dark:border-red-800">
        <AlertTriangle size={24} className="text-red-600 flex-shrink-0" />
        <div>
          <h1 className="text-xl font-bold text-red-700 dark:text-red-400">Emergency Health Support</h1>
          <p className="text-sm text-red-600 dark:text-red-500">For life-threatening emergencies, call 108 immediately. Do not delay seeking help.</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {emergencyNumbers.map(({ label, number, color, desc }) => (
          <motion.a key={label} href={`tel:${number.replace(/[^0-9]/g, '')}`}
            whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            className={`${color} text-white rounded-2xl p-4 flex flex-col gap-2 shadow-lg cursor-pointer`}>
            <Phone size={20} />
            <p className="text-2xl font-bold">{number}</p>
            <p className="font-semibold text-sm">{label}</p>
            <p className="text-xs opacity-80">{desc}</p>
          </motion.a>
        ))}
      </div>

      <div className="glass-card p-6">
        <h2 className="font-bold text-slate-800 dark:text-slate-100 text-lg mb-4 flex items-center gap-2">
          <AlertTriangle size={18} className="text-red-500" /> Emergency Warning Signs
        </h2>
        <div className="space-y-3">
          {warningSigns.map(({ sign, action }) => (
            <div key={sign} className="flex items-start gap-3 p-3 bg-red-50 dark:bg-red-900/10 rounded-xl">
              <AlertTriangle size={15} className="text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-sm text-slate-800 dark:text-slate-200">{sign}</p>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">{action}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Link to="/hospitals" className="glass-card p-5 flex items-center gap-4 hover:shadow-card-hover transition-all group">
          <div className="w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center">
            <MapPin size={22} className="text-blue-600" />
          </div>
          <div>
            <p className="font-semibold text-slate-800 dark:text-slate-100">Find Nearest Hospital</p>
            <p className="text-xs text-slate-500">Locate emergency rooms and clinics nearby</p>
          </div>
        </Link>
        <Link to="/chat" className="glass-card p-5 flex items-center gap-4 hover:shadow-card-hover transition-all group">
          <div className="w-12 h-12 rounded-xl bg-teal-50 dark:bg-teal-900/20 flex items-center justify-center">
            <MessageSquare size={22} className="text-teal-600" />
          </div>
          <div>
            <p className="font-semibold text-slate-800 dark:text-slate-100">AI Medical Assistant</p>
            <p className="text-xs text-slate-500">Get immediate guidance on symptoms</p>
          </div>
        </Link>
      </div>

      <p className="text-xs text-center text-slate-400">HomeCare+ is not a substitute for emergency medical services. In an emergency, always call 108 or go to the nearest emergency room.</p>
    </div>
  )
}
