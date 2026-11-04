import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Mail, Lock, ArrowRight } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const { login, isLoading } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await login(form.email, form.password)
    if (result.success) navigate('/dashboard')
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mb-1">Welcome back</h2>
      <p className="text-slate-500 dark:text-slate-400 text-sm mb-8">Sign in to your HomeCare+ account</p>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Email Address</label>
          <div className="relative">
            <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="input-field pl-10"
              placeholder="you@example.com"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Password</label>
          <div className="relative">
            <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type={showPassword ? 'text' : 'password'}
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="input-field pl-10 pr-10"
              placeholder="Enter your password"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" className="rounded border-slate-300 text-blue-600" />
            <span className="text-sm text-slate-600 dark:text-slate-400">Remember me</span>
          </label>
          <a href="#" className="text-sm font-medium text-blue-600 hover:text-blue-700">Forgot password?</a>
        </div>

        <button type="submit" disabled={isLoading} className="btn-primary w-full justify-center py-3.5">
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z"/>
              </svg>
              Signing in...
            </span>
          ) : (
            <span className="flex items-center gap-2">Sign In <ArrowRight size={16} /></span>
          )}
        </button>
      </form>

      <p className="text-center mt-6 text-sm text-slate-500 dark:text-slate-400">
        Don't have an account?{' '}
        <Link to="/register" className="font-semibold text-blue-600 hover:text-blue-700">Create account</Link>
      </p>

      {/* Demo credentials */}
      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-100 dark:border-blue-800">
        <p className="text-xs font-semibold text-blue-700 dark:text-blue-400 mb-1">Demo Credentials</p>
        <p className="text-xs text-blue-600 dark:text-blue-300">Email: demo@homecare.plus</p>
        <p className="text-xs text-blue-600 dark:text-blue-300">Password: Demo@1234</p>
      </div>
    </div>
  )
}
