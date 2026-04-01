import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'

const NAV_ITEMS = [
  { id: 'inicio', icon: '🏠', label: 'Inicio' },
  { id: 'mercados', icon: '📈', label: 'Mercados Reales' },
  { id: 'laliga', icon: '🏆', label: 'La Liga' },
  { id: 'segunda', icon: '🥈', label: 'Segunda División' },
  { id: 'favoritos', icon: '⭐', label: 'Mis Favoritos' },
  { id: 'tipsters', icon: '👤', label: 'Tipsters' },
  { id: 'perfil', icon: '⚙️', label: 'Mi Perfil' },
]

export default function Sidebar({ activeSection, setActiveSection }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/')
  }

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="px-6 py-6 border-b border-white/5">
        <span className="text-lg font-bold text-white">⚽ LaLigaMarkets</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = activeSection === item.id
          return (
            <button
              key={item.id}
              onClick={() => {
                setActiveSection(item.id)
                setMobileOpen(false)
              }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all text-left ${
                isActive
                  ? 'bg-emerald-500/10 text-emerald-400 border-l-4 border-emerald-500'
                  : 'text-slate-400 hover:text-white hover:bg-white/5 border-l-4 border-transparent'
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </button>
          )
        })}
      </nav>

      {/* Logout */}
      <div className="px-3 py-4 border-t border-white/5">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-red-400 hover:bg-red-400/10 transition-all text-left border-l-4 border-transparent"
        >
          <span className="text-base">🚪</span>
          Cerrar Sesión
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile hamburger */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="fixed top-4 left-4 z-50 lg:hidden bg-[#1E293B] border border-white/10 p-2 rounded-xl text-white"
      >
        <div className="w-5 h-0.5 bg-white mb-1" />
        <div className="w-5 h-0.5 bg-white mb-1" />
        <div className="w-5 h-0.5 bg-white" />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <div
        className={`fixed top-0 left-0 h-full z-40 w-64 bg-[#1E293B] border-r border-white/5 transition-transform duration-300 lg:hidden ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {sidebarContent}
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:flex w-64 min-h-screen bg-[#1E293B] border-r border-white/5 flex-col flex-shrink-0">
        {sidebarContent}
      </div>
    </>
  )
}
