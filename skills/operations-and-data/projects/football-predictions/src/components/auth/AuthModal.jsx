import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'

export default function AuthModal({ isOpen, onClose, initialView = 'login' }) {
  const [view, setView] = useState(initialView)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [terms, setTerms] = useState(false)
  const [error, setError] = useState('')

  const login = useAuthStore((s) => s.login)
  const navigate = useNavigate()

  if (!isOpen) return null

  function handleLogin(e) {
    e.preventDefault()
    setError('')
    if (!email || !password) {
      setError('Rellena todos los campos.')
      return
    }
    login(email)
    onClose()
    navigate('/dashboard')
  }

  function handleSignup(e) {
    e.preventDefault()
    setError('')
    if (!email || !password || !confirm) {
      setError('Rellena todos los campos.')
      return
    }
    if (password !== confirm) {
      setError('Las contraseñas no coinciden.')
      return
    }
    if (!terms) {
      setError('Debes aceptar los términos.')
      return
    }
    login(email)
    onClose()
    navigate('/dashboard')
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="relative w-full max-w-md mx-4 bg-[#1E293B] rounded-2xl shadow-2xl p-8">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors text-2xl leading-none"
        >
          ×
        </button>

        {/* Logo */}
        <div className="text-center mb-6">
          <span className="text-2xl font-bold text-white">⚽ LaLigaMarkets</span>
        </div>

        {/* Tabs */}
        <div className="flex mb-6 bg-[#0F172A] rounded-xl p-1">
          <button
            onClick={() => { setView('login'); setError('') }}
            className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all ${
              view === 'login'
                ? 'bg-emerald-500 text-white'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Iniciar Sesión
          </button>
          <button
            onClick={() => { setView('signup'); setError('') }}
            className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all ${
              view === 'signup'
                ? 'bg-emerald-500 text-white'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Registrarse
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            {error}
          </div>
        )}

        {view === 'login' ? (
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-slate-400 text-sm mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="tu@email.com"
                className="w-full bg-[#0F172A] border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
            <div>
              <label className="block text-slate-400 text-sm mb-1">Contraseña</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#0F172A] border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
            <button
              type="submit"
              className="w-full bg-emerald-500 hover:bg-emerald-400 text-white font-bold py-3 rounded-xl transition-colors"
            >
              Entrar
            </button>
            <p className="text-center text-slate-400 text-sm">
              <button type="button" className="text-emerald-400 hover:underline">
                ¿Olvidaste tu contraseña?
              </button>
            </p>
          </form>
        ) : (
          <form onSubmit={handleSignup} className="space-y-4">
            <div>
              <label className="block text-slate-400 text-sm mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="tu@email.com"
                className="w-full bg-[#0F172A] border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
            <div>
              <label className="block text-slate-400 text-sm mb-1">Contraseña</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#0F172A] border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
            <div>
              <label className="block text-slate-400 text-sm mb-1">Confirmar Contraseña</label>
              <input
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#0F172A] border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={terms}
                onChange={(e) => setTerms(e.target.checked)}
                className="w-4 h-4 accent-emerald-500"
              />
              <span className="text-slate-400 text-sm">
                Acepto los{' '}
                <span className="text-emerald-400 hover:underline cursor-pointer">
                  Términos y Condiciones
                </span>
              </span>
            </label>
            <button
              type="submit"
              className="w-full bg-emerald-500 hover:bg-emerald-400 text-white font-bold py-3 rounded-xl transition-colors"
            >
              Crear Cuenta
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
