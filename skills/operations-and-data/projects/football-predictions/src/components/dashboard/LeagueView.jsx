import { useEffect, useState } from 'react'
import { fetchMatches, fetchRecentMatches } from '../../api/football'
import MatchCard from './MatchCard'

function SkeletonCard() {
  return (
    <div className="bg-[#1E293B] rounded-xl p-4 animate-pulse">
      <div className="h-3 bg-slate-700 rounded w-1/3 mb-3" />
      <div className="flex justify-between items-center">
        <div className="flex flex-col items-center gap-2 flex-1">
          <div className="w-12 h-12 rounded-full bg-slate-700" />
          <div className="h-3 bg-slate-700 rounded w-20" />
        </div>
        <div className="h-6 bg-slate-700 rounded w-16" />
        <div className="flex flex-col items-center gap-2 flex-1">
          <div className="w-12 h-12 rounded-full bg-slate-700" />
          <div className="h-3 bg-slate-700 rounded w-20" />
        </div>
      </div>
    </div>
  )
}

export default function LeagueView({ league }) {
  const [upcoming, setUpcoming] = useState([])
  const [recent, setRecent] = useState([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('upcoming')

  const leagueLabel = league === 'laliga' ? 'La Liga' : 'Segunda División'

  useEffect(() => {
    setLoading(true)
    Promise.all([
      fetchMatches(league, 21),
      fetchRecentMatches(league, 14),
    ]).then(([up, rec]) => {
      setUpcoming(up)
      setRecent(rec)
      setLoading(false)
    })
  }, [league])

  const matches = tab === 'upcoming' ? upcoming : recent

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-white font-bold text-xl">{leagueLabel}</h2>
          <p className="text-slate-400 text-sm">Partidos reales — datos ESPN</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setTab('upcoming')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === 'upcoming' ? 'bg-emerald-500 text-white' : 'bg-[#1E293B] text-slate-400 hover:text-white'}`}
          >
            Próximos
          </button>
          <button
            onClick={() => setTab('recent')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === 'recent' ? 'bg-emerald-500 text-white' : 'bg-[#1E293B] text-slate-400 hover:text-white'}`}
          >
            Recientes
          </button>
        </div>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array(6).fill(0).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : matches.length === 0 ? (
        <div className="bg-[#1E293B] rounded-xl p-12 text-center text-slate-400">
          No hay partidos disponibles para este período.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {matches.map((match) => (
            <MatchCard key={match.id} match={match} />
          ))}
        </div>
      )}
    </div>
  )
}
