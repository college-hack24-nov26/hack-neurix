import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Shield, FileText } from 'lucide-react'

export default function Legal() {
  const { pathname } = useLocation()
  const type = pathname.includes('privacy') ? 'privacy' : 'terms'
  const isPrivacy = type === 'privacy'

  return (
    <main className="min-h-screen bg-slate-50 dark:bg-slate-950 px-4 py-12">
      <article className="max-w-3xl mx-auto glass-card p-6 sm:p-10">
        <div className="flex items-center gap-3 mb-6">
          {isPrivacy ? <Shield className="text-blue-600" /> : <FileText className="text-blue-600" />}
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
            {isPrivacy ? 'Privacy Policy' : 'Terms of Service'}
          </h1>
        </div>
        {isPrivacy ? (
          <div className="space-y-4 text-sm text-slate-600 dark:text-slate-300">
            <p>HomeCare+ stores account details, health records, uploaded files, vitals, activity history, and application preferences needed to provide the service.</p>
            <p>Data is used to operate the requested features and improve the current session experience. Do not upload documents containing information you do not have permission to share.</p>
            <p>You may delete health records and activity history from within the application. Account and data deletion requests require an administrator or a future in-product account deletion workflow.</p>
            <p>HomeCare+ is an educational support application and does not replace professional medical care.</p>
          </div>
        ) : (
          <div className="space-y-4 text-sm text-slate-600 dark:text-slate-300">
            <p>By using HomeCare+, you agree to use the application lawfully and provide accurate information.</p>
            <p>Symptom checks, AI answers, image analysis, report summaries, and health scores are informational and may be inaccurate. Seek advice from a qualified healthcare professional for diagnosis or treatment.</p>
            <p>Emergency features do not replace emergency medical services. Contact local emergency services when immediate help is required.</p>
            <p>Features labeled as bookings or directories may be demonstrations or depend on third-party providers and are not guarantees of medical service availability.</p>
          </div>
        )}
        <Link to="/" className="inline-block mt-8 text-sm font-medium text-blue-600 hover:underline">Back to HomeCare+</Link>
      </article>
    </main>
  )
}
