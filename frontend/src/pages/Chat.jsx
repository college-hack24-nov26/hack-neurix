import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Trash2, Download, AlertCircle, Paperclip, Volume2, Square } from 'lucide-react'
import { chatService } from '../services/api'
import { useAuthStore } from '../store/authStore'
import { useThemeStore } from '../store/themeStore'
import { useTranslation } from 'react-i18next'

const suggestedQuestions = [
  'What are the symptoms of diabetes?',
  'How can I lower my blood pressure naturally?',
  'What should I eat to improve my immunity?',
  'When should I see a doctor for a headache?',
  'What are early signs of heart disease?',
  'How can I manage stress and anxiety?',
]

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-teal-500 flex items-center justify-center flex-shrink-0">
        <Bot size={15} className="text-white" />
      </div>
      <div className="bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-2xl rounded-bl-sm px-4 py-3">
        <div className="flex gap-1.5 items-center h-5">
          {[0, 1, 2].map((i) => (
            <motion.span key={i} className="w-2 h-2 bg-slate-400 rounded-full"
              animate={{ y: [0, -6, 0] }}
              transition={{ duration: 0.6, delay: i * 0.15, repeat: Infinity }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

function ChatMessage({ msg, index, isSpeaking, onSpeak }) {
  const isUser = msg.role === 'user'
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex items-end gap-2.5 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-blue-600' : msg.isError ? 'bg-red-500' : 'bg-gradient-to-br from-blue-500 to-teal-500'
      }`}>
        {isUser ? <User size={15} className="text-white" /> : <Bot size={15} className="text-white" />}
      </div>
      <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
        isUser
          ? 'bg-blue-600 text-white rounded-br-sm'
          : msg.isError
            ? 'bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800 text-red-700 dark:text-red-300 rounded-bl-sm'
            : 'bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 text-slate-700 dark:text-slate-300 rounded-bl-sm'
      }`}>
        <p style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</p>
        <div className="flex items-center gap-2 mt-1.5">
          <p className={`text-xs ${isUser ? 'text-blue-200' : 'text-slate-400'}`}>
            {new Date(msg.timestamp || msg.created_at || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
          {!isUser && msg.aiPowered === false && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400">
              Offline mode
            </span>
          )}
          {!isUser && !msg.isError && (
            <button
              type="button"
              onClick={() => onSpeak(msg.content, index)}
              aria-label={isSpeaking ? 'Stop reading response aloud' : 'Read full response aloud'}
              title={isSpeaking ? 'Stop reading' : 'Read aloud'}
              className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs text-slate-500 hover:bg-slate-100 hover:text-blue-600 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-blue-400"
            >
              {isSpeaking ? <Square size={12} /> : <Volume2 size={14} />}
              <span>{isSpeaking ? 'Stop' : 'Listen'}</span>
            </button>
          )}
        </div>
      </div>
    </motion.div>
  )
}

export default function Chat() {
  const { user } = useAuthStore()
  const { language } = useThemeStore()
  const { t } = useTranslation()
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hello ${user?.firstName || 'there'}! I'm your HomeCare+ AI Medical Assistant.\n\nI can help you with:\n• Understanding symptoms and diseases\n• Health and wellness advice\n• Medication information\n• Navigating the platform\n\nHow can I assist you today? Please remember that I provide health information only and am not a substitute for professional medical advice.`,
      timestamp: new Date().toISOString(),
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [speakingMessage, setSpeakingMessage] = useState(null)
  const bottomRef = useRef(null)
  const speechRunRef = useRef(0)

  const stopSpeaking = () => {
    speechRunRef.current += 1
    window.speechSynthesis?.cancel()
    setSpeakingMessage(null)
  }

  const speakMessage = (content, messageIndex) => {
    if (!('speechSynthesis' in window) || !('SpeechSynthesisUtterance' in window)) return
    if (speakingMessage === messageIndex) {
      stopSpeaking()
      return
    }

    window.speechSynthesis.cancel()
    const runId = speechRunRef.current + 1
    speechRunRef.current = runId
    setSpeakingMessage(messageIndex)

    const plainText = content
      .replace(/```[\s\S]*?```/g, (block) => block.replace(/```[^\n]*\n?/, '').replace(/```$/, ''))
      .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
      .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
      .replace(/https?:\/\/\S+/g, '')
      .replace(/^\s{0,3}#{1,6}\s+/gm, '')
      .replace(/(\*\*|__|~~|`|\*|_)/g, '')
      .replace(/^\s*[-*+]\s+/gm, '')
      .replace(/^\s*\d+[.)]\s+/gm, '')
      .replace(/\s+/g, ' ')
      .trim()
    const sentences = plainText.match(/[^.!?।]+[.!?।]*/g) || [plainText]
    const chunks = []
    let chunk = ''
    sentences.forEach((sentence) => {
      const words = sentence.trim().split(/\s+/)
      words.forEach((word) => {
        if (chunk && `${chunk} ${word}`.length > 220) {
          chunks.push(chunk)
          chunk = word
        } else {
          chunk = chunk ? `${chunk} ${word}` : word
        }
      })
    })
    if (chunk) chunks.push(chunk)

    const locale = language === 'hi-latn' ? 'en-IN' : ({
      en: 'en-US', hi: 'hi-IN', mr: 'mr-IN', ta: 'ta-IN', te: 'te-IN',
      kn: 'kn-IN', ml: 'ml-IN', gu: 'gu-IN', ur: 'ur-PK', bn: 'bn-IN', pa: 'pa-IN',
    }[language] || 'en-US')
    const voices = window.speechSynthesis.getVoices()
    const voice = voices.find((item) => item.lang.toLowerCase() === locale.toLowerCase())
      || voices.find((item) => item.lang.toLowerCase().startsWith(locale.split('-')[0].toLowerCase()))

    const speakChunk = (index) => {
      if (speechRunRef.current !== runId || index >= chunks.length) {
        if (speechRunRef.current === runId) setSpeakingMessage(null)
        return
      }
      const utterance = new SpeechSynthesisUtterance(chunks[index])
      utterance.lang = locale
      if (voice) utterance.voice = voice
      utterance.onend = () => speakChunk(index + 1)
      utterance.onerror = () => {
        if (speechRunRef.current === runId) setSpeakingMessage(null)
      }
      window.speechSynthesis.speak(utterance)
    }

    if (chunks.length) speakChunk(0)
    else setSpeakingMessage(null)
  }

  useEffect(() => () => {
    speechRunRef.current += 1
    window.speechSynthesis?.cancel()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = async (text) => {
    const msg = text || input.trim()
    if (!msg || loading) return
    setInput('')

    const userMsg = { role: 'user', content: msg, timestamp: new Date().toISOString() }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    try {
      const history = [...messages, userMsg].map(({ role, content }) => ({ role, content }))
      const { data } = await chatService.sendMessage(history, language)
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        aiPowered: data.ai_powered,
      }])
    } catch (err) {
      const msg = err.response?.data?.detail || 'Sorry, something went wrong reaching the AI assistant. Please try again.'
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: msg,
        timestamp: new Date().toISOString(),
        isError: true,
      }])
    } finally {
      setLoading(false)
    }
  }

  const clearChat = async () => {
    try {
      await chatService.clearHistory()
    } catch {
      // Non-fatal — still reset local view even if server call fails
    }
    stopSpeaking()
    setMessages([{
      role: 'assistant',
      content: 'Chat history cleared. How can I assist you with your health today?',
      timestamp: new Date().toISOString(),
    }])
  }

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)] max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-teal-500 flex items-center justify-center">
            <Bot size={20} className="text-white" />
          </div>
          <div>
            <h1 className="font-bold text-slate-800 dark:text-slate-100">AI Medical Assistant</h1>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-xs text-green-600 dark:text-green-400 font-medium">Online</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={clearChat} className="btn-secondary text-xs px-3 py-2">
            <Trash2 size={14} /> Clear
          </button>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-100 dark:border-amber-800 mb-4 flex-shrink-0">
        <AlertCircle size={15} className="text-amber-600 flex-shrink-0" />
        <p className="text-xs text-amber-700 dark:text-amber-400">
          This AI assistant provides general health information only. It does not replace professional medical advice.
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-5 pr-2 no-scrollbar glass-card p-5">
        {messages.map((msg, i) => (
          <ChatMessage
            key={i}
            msg={msg}
            index={i}
            isSpeaking={speakingMessage === i}
            onSpeak={speakMessage}
          />
        ))}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Suggested questions */}
      {messages.length <= 1 && (
        <div className="mt-4 mb-3">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Suggested Questions</p>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((q) => (
              <button key={q} onClick={() => sendMessage(q)}
                className="text-xs px-3 py-1.5 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-blue-800 hover:bg-blue-100 transition-colors">
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="mt-4 flex gap-3">
        <div className="flex-1 flex items-center gap-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl px-4 py-3 focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100 dark:focus-within:ring-blue-900 transition-all">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
            placeholder="Ask about symptoms, diseases, health advice..."
            className="flex-1 bg-transparent text-sm text-slate-700 dark:text-slate-300 placeholder-slate-400 outline-none"
          />
        </div>
        <button
          onClick={() => sendMessage()}
          disabled={!input.trim() || loading}
          className="btn-primary px-4 py-3 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  )
}
