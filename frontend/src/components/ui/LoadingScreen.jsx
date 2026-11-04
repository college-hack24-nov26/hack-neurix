import React from 'react'
import { motion } from 'framer-motion'

export default function LoadingScreen() {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-white dark:bg-slate-900 z-50">
      <div className="flex flex-col items-center gap-6">
        {/* Animated logo mark */}
        <motion.div
          className="relative"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-medical-green flex items-center justify-center shadow-glow">
            <svg viewBox="0 0 32 32" fill="none" className="w-9 h-9">
              <path d="M16 4v24M4 16h24" stroke="white" strokeWidth="3" strokeLinecap="round"/>
              <circle cx="16" cy="16" r="12" stroke="white" strokeWidth="2" opacity="0.3"/>
            </svg>
          </div>
          {/* Pulse rings */}
          {[1, 2, 3].map((i) => (
            <motion.div
              key={i}
              className="absolute inset-0 rounded-2xl border-2 border-blue-400"
              initial={{ scale: 1, opacity: 0.6 }}
              animate={{ scale: 1.5 + i * 0.3, opacity: 0 }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                delay: i * 0.3,
                ease: 'easeOut',
              }}
            />
          ))}
        </motion.div>

        <motion.div
          className="flex flex-col items-center gap-2"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">
            HomeCare<span className="text-blue-600">+</span>
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Loading your health companion...
          </p>
        </motion.div>

        {/* Loading bar */}
        <motion.div className="w-48 h-1 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-blue-600 to-medical-green rounded-full"
            initial={{ x: '-100%' }}
            animate={{ x: '100%' }}
            transition={{ duration: 1.2, repeat: Infinity, ease: 'easeInOut' }}
          />
        </motion.div>
      </div>
    </div>
  )
}
