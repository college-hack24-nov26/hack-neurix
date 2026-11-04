import React from 'react'
import { Outlet, Link } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function AuthLayout() {
  return (
    <div className="min-h-screen flex">
      {/* Left panel - branding */}
      <div className="hidden lg:flex flex-col w-1/2 gradient-bg p-12 relative overflow-hidden">
        {/* Background circles */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />

        <Link to="/" className="flex items-center gap-3 z-10">
          <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center">
            <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
              <path d="M12 3v18M3 12h18" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
            </svg>
          </div>
          <span className="text-xl font-bold text-white">HomeCare+</span>
        </Link>

        <div className="flex-1 flex flex-col justify-center z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl font-bold text-white leading-tight mb-4">
              Your Digital Healthcare Companion
            </h1>
            <p className="text-blue-100 text-lg leading-relaxed mb-8">
              AI-powered symptom analysis, health monitoring, medical records, and personalized health insights — all in one place.
            </p>

            <div className="grid grid-cols-2 gap-4">
              {[
                { label: 'Diseases Covered', value: '2,000+' },
                { label: 'Symptoms Analyzed', value: '500+' },
                { label: 'Languages', value: '7' },
                { label: 'AI Accuracy', value: '94%' },
              ].map(({ label, value }) => (
                <div key={label} className="bg-white/10 backdrop-blur rounded-xl p-4">
                  <p className="text-2xl font-bold text-white">{value}</p>
                  <p className="text-blue-100 text-sm">{label}</p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        <p className="text-blue-200 text-xs z-10">
          Always consult a qualified healthcare professional for medical decisions.
        </p>
      </div>

      {/* Right panel - form */}
      <div className="flex-1 flex items-center justify-center p-6 bg-slate-50 dark:bg-slate-900">
        <motion.div
          className="w-full max-w-md"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
        >
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center">
              <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
                <path d="M12 3v18M3 12h18" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
              </svg>
            </div>
            <span className="text-xl font-bold text-slate-800 dark:text-slate-100">
              HomeCare<span className="text-blue-600">+</span>
            </span>
          </div>
          <Outlet />
        </motion.div>
      </div>
    </div>
  )
}
