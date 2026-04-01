import { useState } from 'react'

function TeamLogo({ logo, name, size = 'md' }) {
  const [imgErr, setImgErr] = useState(false)
  const sz = size === 'sm' ? 'w-8 h-8 text-xs' : 'w-12 h-12 text-sm'
  if (logo && !imgErr) {
    return (
      <img
        src={logo}
        alt={name}
        className={`${sz} object-contain`}
        onError={() => setImgErr(true)}
      />
    )
  }
  return (
    <div className={`${sz} rounded-full bg-slate-700 flex items-center justify-center font-bold text-slate-300`}>
      {name?.slice(0, 2).toUpperCase()}
    </div>
  )
}

export default function MatchCard({ match, onClick }) {
  const dateObj = new Date(match.date)
  const dateStr = dateObj.toLocaleDateString('es-ES', { weekday: 'short', day: 'numeric', month: 'short' })
  const timeStr = dateObj.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })

  return (
    <div
      className="bg-[#1E293B] rounded-xl p-4 hover:bg-slate-700/50 transition-all cursor-pointer border border-transparent hover:border-emerald-500/30"
      onClick={() => onClick?.(match)}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-slate-400">{match.round || (match.league === 'laliga' ? 'La Liga' : 'Segunda División')}</span>
        <div className="flex items-center gap-2">
          {match.isLive && (
            <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-red-500/20 text-red-400 animate-pulse">
              EN VIVO
            </span>
          )}
          <span className="text-xs text-slate-400">{match.isFinished ? 'Finalizado' : `${dateStr} ${timeStr}`}</span>
        </div>
      </div>

      {/* Teams */}
      <div className="flex items-center justify-between gap-2">
        {/* Home */}
        <div className="flex-1 flex flex-col items-center gap-2 text-center">
          <TeamLogo logo={match.home.logo} name={match.home.name} />
          <span className="text-white text-sm font-medium leading-tight">{match.home.shortName || match.home.name}</span>
        </div>

        {/* Score / VS */}
        <div className="flex flex-col items-center px-3">
          {match.isFinished || match.isLive ? (
            <span className="text-white text-2xl font-bold tabular-nums">
              {match.home.score ?? 0} - {match.away.score ?? 0}
            </span>
          ) : (
            <div className="text-center">
              <span className="text-white font-bold text-lg">VS</span>
              <p className="text-slate-400 text-xs mt-1">{timeStr}</p>
            </div>
          )}
        </div>

        {/* Away */}
        <div className="flex-1 flex flex-col items-center gap-2 text-center">
          <TeamLogo logo={match.away.logo} name={match.away.name} />
          <span className="text-white text-sm font-medium leading-tight">{match.away.shortName || match.away.name}</span>
        </div>
      </div>

      {/* Footer */}
      {match.venue && (
        <p className="text-slate-500 text-xs text-center mt-3 truncate">📍 {match.venue}</p>
      )}
    </div>
  )
}
