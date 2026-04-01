import { useState, useEffect } from 'react'
import Sidebar from '../components/layout/Sidebar'
import LeagueView from '../components/dashboard/LeagueView'
import MatchCard from '../components/dashboard/MatchCard'
import TipsterCard from '../components/dashboard/TipsterCard'
import SeasonMarkets from '../components/dashboard/SeasonMarkets'
import { fetchMatches, MOCK_TIPSTERS } from '../api/football'
import useAuthStore from '../store/authStore'
import { useNavigate } from 'react-router-dom'

// ── Section Components ──────────────────────────────────────────────────────

function Inicio({ userName, activeSection }) {
  const [homeMatches, setHomeMatches] = useState([])
  const [loadingHome, setLoadingHome] = useState(true)

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Buenos días' : hour < 20 ? 'Buenas tardes' : 'Buenas noches'

  useEffect(() => {
    if (activeSection === 'inicio') {
      Promise.all([fetchMatches('laliga', 10), fetchMatches('segunda', 10)]).then(([la, seg]) => {
        setHomeMatches([...la, ...seg].sort((a, b) => new Date(a.date) - new Date(b.date)).slice(0, 9))
        setLoadingHome(false)
      })
    }
  }, [activeSection])

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-black text-white">
          {greeting},{' '}
          <span className="text-emerald-400 capitalize">{userName}</span> 👋
        </h1>
        <p className="text-slate-400 mt-1">
          {new Date().toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
        </p>
      </div>

      {/* Upcoming matches */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <h2 className="text-lg font-bold text-white">Próximos Partidos</h2>
          {!loadingHome && (
            <span className="text-xs bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full">
              {homeMatches.length} partidos
            </span>
          )}
        </div>
        {loadingHome ? (
          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
            {Array(6).fill(0).map((_, i) => (
              <div key={i} className="bg-[#1E293B] rounded-xl p-4 animate-pulse h-40" />
            ))}
          </div>
        ) : homeMatches.length === 0 ? (
          <div className="bg-[#1E293B] rounded-xl p-12 text-center text-slate-400">
            No hay partidos disponibles en este momento.
          </div>
        ) : (
          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
            {homeMatches.map((match) => (
              <MatchCard key={match.id} match={match} />
            ))}
          </div>
        )}
      </div>

      {/* Season markets */}
      <div className="mt-10">
        <SeasonMarkets />
      </div>
    </div>
  )
}

function Favoritos() {
  return (
    <div className="flex flex-col items-center justify-center py-32 text-center">
      <div className="text-6xl mb-4">⭐</div>
      <h2 className="text-2xl font-bold text-white mb-2">Sin favoritos aún</h2>
      <p className="text-slate-400 max-w-sm">
        Guarda partidos en tus favoritos pulsando el icono de estrella en cualquier MatchCard para acceder a ellos rápidamente.
      </p>
    </div>
  )
}

function Tipsters() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-1">👤 Tipsters</h2>
        <p className="text-slate-400 text-sm">
          Sigue a los mejores analistas de La Liga y Segunda División
        </p>
      </div>

      {/* Leaderboard */}
      <div className="bg-[#1E293B] rounded-2xl border border-white/5 mb-8 overflow-hidden">
        <div className="px-5 py-4 border-b border-white/5">
          <h3 className="text-white font-bold">🏆 Ranking por Hit Rate</h3>
        </div>
        <div className="divide-y divide-white/5">
          {MOCK_TIPSTERS.sort((a, b) => b.hitRate - a.hitRate).map((t, i) => (
            <div key={t.id} className="px-5 py-3 flex items-center gap-4 hover:bg-white/2 transition-colors">
              <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                i === 0 ? 'bg-amber-500/20 text-amber-400' :
                i === 1 ? 'bg-slate-500/20 text-slate-300' :
                i === 2 ? 'bg-orange-500/20 text-orange-400' :
                'bg-slate-800 text-slate-500'
              }`}>
                {i + 1}
              </span>
              <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-xs">
                {t.avatar}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-white font-semibold text-sm">{t.name}</div>
                <div className="text-slate-500 text-xs">{t.specialty}</div>
              </div>
              <div className="text-right hidden sm:block">
                <div className="text-emerald-400 font-bold text-sm">{t.hitRate}%</div>
                <div className="text-slate-500 text-xs">{t.totalPicks} picks</div>
              </div>
              <div className="text-right hidden md:block">
                <div className="text-amber-400 font-bold text-sm">+{t.roi}%</div>
                <div className="text-slate-500 text-xs">ROI</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Cards grid */}
      <h3 className="text-white font-bold mb-4">Todos los Tipsters</h3>
      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-4">
        {MOCK_TIPSTERS.map((t) => (
          <TipsterCard key={t.id} tipster={t} />
        ))}
      </div>
    </div>
  )
}

function Perfil() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()
  const [name, setName] = useState(user?.name || '')
  const [email, setEmail] = useState(user?.email || '')
  const [saved, setSaved] = useState(false)

  function handleSave(e) {
    e.preventDefault()
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-1">⚙️ Mi Perfil</h2>
        <p className="text-slate-400 text-sm">Gestiona tu cuenta y suscripción</p>
      </div>

      {/* Plan info */}
      <div className="bg-gradient-to-br from-emerald-900/30 to-[#1E293B] border border-emerald-500/30 rounded-2xl p-5 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs text-emerald-400 font-semibold uppercase tracking-wider mb-1">Plan Activo</div>
            <div className="text-white font-bold text-xl">Pro Bettor</div>
            <div className="text-slate-400 text-sm mt-1">
              Renueva el 26 de abril de 2026 · €5/mes
            </div>
          </div>
          <div className="w-14 h-14 rounded-full bg-emerald-500/20 flex items-center justify-center text-3xl">
            🏆
          </div>
        </div>
      </div>

      {/* Profile form */}
      <div className="bg-[#1E293B] rounded-2xl p-6 border border-white/5 mb-4">
        <h3 className="text-white font-bold mb-5">Información Personal</h3>
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-slate-400 text-sm mb-1">Nombre</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-[#0F172A] border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>
          <div>
            <label className="block text-slate-400 text-sm mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-[#0F172A] border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>
          <div>
            <label className="block text-slate-400 text-sm mb-1">Nueva Contraseña</label>
            <input
              type="password"
              placeholder="Dejar en blanco para mantener actual"
              className="w-full bg-[#0F172A] border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>
          <button
            type="submit"
            className="w-full py-3 bg-emerald-500 hover:bg-emerald-400 text-white font-bold rounded-xl transition-colors"
          >
            {saved ? '✓ Guardado' : 'Guardar Cambios'}
          </button>
        </form>
      </div>

      <button
        onClick={handleLogout}
        className="w-full py-3 border border-red-500/40 text-red-400 hover:bg-red-500/10 rounded-xl font-semibold transition-colors"
      >
        🚪 Cerrar Sesión
      </button>
    </div>
  )
}

// ── Main Dashboard ──────────────────────────────────────────────────────────

export default function Dashboard() {
  const [activeSection, setActiveSection] = useState('inicio')
  const user = useAuthStore((s) => s.user)

  function renderSection() {
    switch (activeSection) {
      case 'inicio':    return <Inicio userName={user?.name || 'Usuario'} activeSection={activeSection} />
      case 'laliga':    return <LeagueView league="laliga" />
      case 'segunda':   return <LeagueView league="segunda" />
      case 'mercados':  return <SeasonMarkets />
      case 'favoritos': return <Favoritos />
      case 'tipsters':  return <Tipsters />
      case 'perfil':    return <Perfil />
      default:          return <Inicio userName={user?.name || 'Usuario'} activeSection={activeSection} />
    }
  }

  return (
    <div className="flex min-h-screen bg-[#0F172A]">
      <Sidebar activeSection={activeSection} setActiveSection={setActiveSection} />
      <main className="flex-1 p-6 lg:p-8 overflow-auto">
        {renderSection()}
      </main>
    </div>
  )
}
