/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Poppins', 'system-ui', 'sans-serif'],
        display: ['Poppins', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        primary: {
          50:  '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
        medical: {
          blue:  '#0066cc',
          green: '#00a878',
          teal:  '#0d9488',
          navy:  '#0a2540',
          light: '#e8f4fd',
        },
        surface: {
          DEFAULT: '#ffffff',
          dark:    '#0f172a',
          card:    '#f8fafc',
          'card-dark': '#1e293b',
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-mesh': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'medical-gradient': 'linear-gradient(135deg, #0066cc 0%, #00a878 100%)',
      },
      boxShadow: {
        card: '0 4px 24px rgba(0,0,0,0.06)',
        'card-hover': '0 8px 40px rgba(0,0,0,0.12)',
        glow: '0 0 20px rgba(59,130,246,0.4)',
        'glow-green': '0 0 20px rgba(0,168,120,0.4)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'gradient': 'gradient 8s ease infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':       { transform: 'translateY(-10px)' },
        },
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%':      { backgroundPosition: '100% 50%' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
