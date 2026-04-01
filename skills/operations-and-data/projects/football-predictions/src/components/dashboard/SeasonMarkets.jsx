import { useEffect, useState } from 'react'
import { fetchSeasonMarkets } from '../../api/football'

export default function SeasonMarkets() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeEvent, setActiveEvent] = useState(null)

  useEffect(() => {
    fetchSeasonMarkets().then((data) => {
      setEvents(data)
      if (data.length > 0) setActiveEvent(data[0].id)
      setLoading(false)
    })
  }, [])

  const fmt = (n) =>
    n >= 1_000_000
      ? `$${(n / 1_000_000).toFixed(1)}M`
      : n >= 1_000
      ? `$${(n / 1_000).toFixed(0)}K`
      : `$${n}`

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        {[1,2,3].map(i => (
          <div key={i} className="h-24 bg-[#1E293B] rounded-xl" />
        ))}
      </div>
    )
  }

  if (!events.length) {
    return (
      <div className="bg-[#1E293B] rounded-xl p-6 text-center text-slate-400">
        No se pudieron cargar los mercados de predicción.
      </div>
    )
  }

  const selected = events.find(e => e.id === activeEvent) ?? events[0]
  // Show top 10 markets by probability
  const topMarkets = selected.markets.slice(0, 10)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-white font-bold text-xl">Apuestas de Temporada</h2>
          <p className="text-slate-400 text-sm mt-1">Datos en tiempo real de mercados de predicción</p>
        </div>
        <a
          href="https://polymarket.com"
          target="_blank"
          rel="noreferrer"
          className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
        >
          Ver mercados →
        </a>
      </div>

      {/* Event tabs */}
      <div className="flex gap-2 flex-wrap">
        {events.map((e) => (
          <button
            key={e.id}
            onClick={() => setActiveEvent(e.id)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              activeEvent === e.id
                ? 'bg-emerald-500 text-white'
                : 'bg-[#1E293B] text-slate-400 hover:text-white'
            }`}
          >
            {e.title}
          </button>
        ))}
      </div>

      {/* Selected event stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-[#1E293B] rounded-xl p-4 text-center">
          <p className="text-slate-400 text-xs mb-1">Volumen Total</p>
          <p className="text-white font-bold text-lg">{fmt(selected.volume)}</p>
        </div>
        <div className="bg-[#1E293B] rounded-xl p-4 text-center">
          <p className="text-slate-400 text-xs mb-1">Volumen 24h</p>
          <p className="text-emerald-400 font-bold text-lg">{fmt(selected.volume24hr)}</p>
        </div>
        <div className="bg-[#1E293B] rounded-xl p-4 text-center">
          <p className="text-slate-400 text-xs mb-1">Mercados Activos</p>
          <p className="text-amber-400 font-bold text-lg">{selected.markets.length}</p>
        </div>
      </div>

      {/* Markets list */}
      <div className="bg-[#1E293B] rounded-xl overflow-hidden">
        <div className="grid grid-cols-12 gap-2 px-4 py-3 text-xs text-slate-400 uppercase tracking-wide border-b border-slate-700">
          <span className="col-span-1">#</span>
          <span className="col-span-5">Equipo / Resultado</span>
          <span className="col-span-4">Probabilidad</span>
          <span className="col-span-2 text-right">Volumen</span>
        </div>
        {topMarkets.map((market, idx) => {
          const pct = market.probability
          const color = pct >= 40 ? 'bg-emerald-500' : pct >= 20 ? 'bg-amber-500' : 'bg-red-500'
          return (
            <div
              key={market.id}
              className="grid grid-cols-12 gap-2 px-4 py-3 items-center border-b border-slate-800 hover:bg-slate-800/30 transition-colors"
            >
              <span className="col-span-1 text-slate-500 text-sm">{idx + 1}</span>
              <div className="col-span-5 flex items-center gap-2">
                {market.image && (
                  <img src={market.image} alt="" className="w-6 h-6 rounded-full object-cover" />
                )}
                <span className="text-white text-sm font-medium truncate">
                  {market.groupItemTitle}
                </span>
              </div>
              <div className="col-span-4 flex items-center gap-2">
                <div className="flex-1 bg-slate-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${color} transition-all`}
                    style={{ width: `${Math.max(pct, 2)}%` }}
                  />
                </div>
                <span className={`text-sm font-bold w-10 text-right ${
                  pct >= 40 ? 'text-emerald-400' : pct >= 20 ? 'text-amber-400' : 'text-red-400'
                }`}>
                  {pct}%
                </span>
              </div>
              <span className="col-span-2 text-right text-slate-400 text-xs">
                {fmt(market.volume)}
              </span>
            </div>
          )
        })}
      </div>

      <p className="text-xs text-slate-500 text-center">
        Probabilidades basadas en mercados de predicción
      </p>
    </div>
  )
}
