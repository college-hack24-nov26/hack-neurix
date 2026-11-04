import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Brain, Heart, Search, FileText, MessageSquare, MapPin,
  Shield, Activity, ChevronRight, Star, Users, Award,
  Stethoscope, Pill, BookOpen, ArrowRight, CheckCircle
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'

const features = [
  {
    icon: Brain,
    title: 'AI Symptom Checker',
    desc: 'Advanced machine learning analyzes your symptoms and predicts possible conditions with probability scores.',
    color: 'from-blue-500 to-blue-600',
  },
  {
    icon: MessageSquare,
    title: 'AI Medical Assistant',
    desc: 'Chat with our intelligent health assistant for instant guidance on diseases, symptoms, and wellness.',
    color: 'from-teal-500 to-teal-600',
  },
  {
    icon: Activity,
    title: 'Health Monitoring',
    desc: 'Track vitals like heart rate, blood pressure, oxygen, blood sugar, and BMI with beautiful dashboards.',
    color: 'from-green-500 to-green-600',
  },
  {
    icon: FileText,
    title: 'Medical Records',
    desc: 'Securely upload and manage prescriptions, lab reports, scans, and health documents.',
    color: 'from-purple-500 to-purple-600',
  },
  {
    icon: MapPin,
    title: 'Hospital Locator',
    desc: 'Find nearby hospitals, clinics, pharmacies, and specialists on an interactive map.',
    color: 'from-orange-500 to-orange-600',
  },
  {
    icon: Shield,
    title: 'Insurance Management',
    desc: 'Store and manage insurance policies, coverage details, and get guidance on claims.',
    color: 'from-indigo-500 to-indigo-600',
  },
]

const stats = [
  { value: '2,000+', label: 'Diseases Covered' },
  { value: '500+',   label: 'Symptoms Mapped' },
  { value: '94%',    label: 'AI Accuracy' },
  { value: '7',      label: 'Languages' },
]

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
}
const item = {
  hidden:  { opacity: 0, y: 20 },
  show:    { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } },
}

export default function Home() {
  const { isAuthenticated } = useAuthStore()

  return (
    <div className="min-h-screen bg-white dark:bg-slate-900">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200/50 dark:border-slate-700/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
                <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5">
                  <path d="M12 3v18M3 12h18" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
                </svg>
              </div>
              <span className="text-lg font-bold text-slate-800 dark:text-slate-100">
                HomeCare<span className="text-blue-600">+</span>
              </span>
            </div>

            <div className="hidden md:flex items-center gap-8">
              {['Features', 'Diseases', 'How It Works', 'About'].map((n) => (
                <a key={n} href={`#${n.toLowerCase().replace(' ', '-')}`}
                  className="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                  {n}
                </a>
              ))}
            </div>

            <div className="flex items-center gap-3">
              {isAuthenticated ? (
                <Link to="/dashboard" className="btn-primary">
                  Go to Dashboard <ChevronRight size={16} />
                </Link>
              ) : (
                <>
                  <Link to="/login" className="btn-secondary">Sign In</Link>
                  <Link to="/register" className="btn-primary">Get Started</Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-28 pb-20 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
        {/* Background gradient blobs */}
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-blue-400/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-40 right-1/4 w-80 h-80 bg-teal-400/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-4xl mx-auto text-center relative">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-sm font-medium mb-6 border border-blue-100 dark:border-blue-800"
          >
            <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            AI-Powered Healthcare Platform
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl md:text-6xl lg:text-7xl font-bold text-slate-900 dark:text-slate-100 leading-tight mb-6"
          >
            Your Digital{' '}
            <span className="text-gradient">Healthcare</span>{' '}
            Companion
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            Analyze symptoms, understand diseases, manage health records, and monitor your wellness — all powered by advanced AI, right from home.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link to="/register" className="btn-primary text-base px-8 py-4">
              Start for Free <ArrowRight size={18} />
            </Link>
            <Link to="/symptom-checker" className="btn-secondary text-base px-8 py-4">
              Try Symptom Checker
            </Link>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-6 text-xs text-slate-400 dark:text-slate-500"
          >
            This platform provides health information only. Always consult a qualified healthcare professional.
          </motion.p>
        </div>

        {/* Stats */}
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="max-w-4xl mx-auto mt-20 grid grid-cols-2 md:grid-cols-4 gap-6"
        >
          {stats.map(({ value, label }) => (
            <motion.div
              key={label}
              variants={item}
              className="glass-card p-6 text-center hover:shadow-card-hover transition-shadow"
            >
              <p className="text-3xl font-bold text-gradient mb-1">{value}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-50 dark:bg-slate-800/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-4">
              Everything You Need for Your Health
            </h2>
            <p className="text-lg text-slate-500 dark:text-slate-400 max-w-2xl mx-auto">
              A comprehensive digital health ecosystem with AI-powered tools designed to help you understand and manage your health.
            </p>
          </div>

          <motion.div
            variants={container}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {features.map(({ icon: Icon, title, desc, color }) => (
              <motion.div
                key={title}
                variants={item}
                className="glass-card p-6 hover:shadow-card-hover transition-all duration-300 group cursor-default"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <Icon size={22} className="text-white" />
                </div>
                <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-2">{title}</h3>
                <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed">{desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="gradient-bg rounded-3xl p-12 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-black/10 rounded-3xl" />
            <div className="relative">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                Start Managing Your Health Today
              </h2>
              <p className="text-blue-100 text-lg mb-8 max-w-xl mx-auto">
                Join thousands of users who trust HomeCare+ for intelligent health management.
              </p>
              <Link to="/register" className="inline-flex items-center gap-2 px-8 py-4 bg-white text-blue-600 rounded-xl font-bold text-base hover:bg-blue-50 transition-colors shadow-lg">
                Create Free Account <ArrowRight size={18} />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-700 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-blue-600 flex items-center justify-center">
              <svg viewBox="0 0 24 24" fill="none" className="w-4 h-4">
                <path d="M12 3v18M3 12h18" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
              </svg>
            </div>
            <span className="font-semibold text-slate-700 dark:text-slate-300">HomeCare+</span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            This platform is for informational purposes only and does not provide medical diagnosis or treatment.
          </p>
          <p className="text-sm text-slate-400 dark:text-slate-500">
            {new Date().getFullYear()} HomeCare+. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  )
}
