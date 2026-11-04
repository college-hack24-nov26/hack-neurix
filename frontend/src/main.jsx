import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App.jsx'
import './index.css'
import './i18n'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3500,
          style: {
            fontFamily: 'Poppins, sans-serif',
            fontSize: '14px',
            fontWeight: '500',
            borderRadius: '12px',
            padding: '12px 16px',
          },
          success: {
            style: { background: '#00a878', color: '#fff' },
            iconTheme: { primary: '#fff', secondary: '#00a878' },
          },
          error: {
            style: { background: '#ef4444', color: '#fff' },
            iconTheme: { primary: '#fff', secondary: '#ef4444' },
          },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
)
