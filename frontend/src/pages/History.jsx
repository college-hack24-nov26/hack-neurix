import React, { useEffect, useState } from 'react'
import { Clock3, Trash2, History as HistoryIcon, Activity, ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { historyService } from '../services/api'

function timeAgo(value) {
  const seconds = Math.floor((Date.now() - new Date(value).getTime()) / 1000)
  if (seconds < 60) return 'Just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} hr ago`
  const days = Math.floor(hours / 24)
  return days === 1 ? 'Yesterday' : `${days} days ago`
}

export default function History() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await historyService.getAll()
      setItems(data.items || [])
    } catch {
      toast.error('Could not load history')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const deleteItem = async (id) => {
    try {
      await historyService.delete(id)
      setItems((current) => current.filter((item) => item.id !== id))
      toast.success('History item deleted')
    } catch {
      toast.error('Could not delete item')
    }
  }

  const clearAll = async () => {
    if (!window.confirm('Delete all your activity history?')) return
    try {
      await historyService.clear()
      setItems([])
      toast.success('History cleared')
    } catch {
      toast.error('Could not clear history')
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-3">
            <HistoryIcon className="text-blue-600" /> History
          </h1>
          <p className="text-slate-500 text-sm mt-1">Your recent activity on HomeCare+</p>
        </div>
        {items.length > 0 && (
          <button onClick={clearAll} className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-red-600 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30">
            <Trash2 size={16} /> Clear all
          </button>
        )}
      </div>

      <div className="glass-card overflow-hidden">
        {loading ? (
          <div className="p-10 text-center text-slate-400">Loading history...</div>
        ) : items.length === 0 ? (
          <div className="p-12 text-center">
            <Clock3 size={40} className="mx-auto text-slate-300 dark:text-slate-600 mb-3" />
            <p className="font-semibold text-slate-700 dark:text-slate-200">No activity yet</p>
            <p className="text-sm text-slate-400 mt-1">Your app usage will appear here.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {items.map((item) => (
              <div key={item.id} className="p-4 sm:p-5 flex items-center gap-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 flex items-center justify-center flex-shrink-0">
                  <Activity size={18} />
                </div>
                <button
                  className="flex-1 text-left min-w-0"
                  onClick={() => item.route && item.route !== '/history' && navigate(item.route)}
                >
                  <p className="font-medium text-slate-800 dark:text-slate-100 text-sm">{item.title}</p>
                  <p className="text-xs text-slate-400 mt-1">{timeAgo(item.created_at)}</p>
                </button>
                {item.route && item.route !== '/history' && <ChevronRight size={16} className="text-slate-300" />}
                <button
                  onClick={() => deleteItem(item.id)}
                  className="p-2 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                  title="Delete history item"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
