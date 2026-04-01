import { useState } from 'react'

export default function TipsterCard({ tipster }) {
  const { name, avatar, hitRate, totalPicks, roi, specialty } = tipster
  const [following, setFollowing] = useState(false)

  return (
    <div className="bg-[#1E293B] rounded-2xl p-5 border border-white/5 hover:border-emerald-500/30 transition-all">
      {/* Avatar + info */}
      <div className="flex items-start gap-4 mb-4">
        <div className="w-12 h-12 rounded-full bg-emerald-500/20 border-2 border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold text-sm flex-shrink-0">
          {avatar}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-white font-bold text-base truncate">{name}</div>
          <span className="inline-block text-xs bg-amber-500/15 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded-full mt-1">
            {specialty}
          </span>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center bg-[#0F172A] rounded-xl py-2">
          <div className="text-emerald-400 font-bold text-lg">{hitRate}%</div>
          <div className="text-slate-500 text-xs">Hit Rate</div>
        </div>
        <div className="text-center bg-[#0F172A] rounded-xl py-2">
          <div className="text-white font-bold text-lg">{totalPicks}</div>
          <div className="text-slate-500 text-xs">Picks</div>
        </div>
        <div className="text-center bg-[#0F172A] rounded-xl py-2">
          <div className="text-amber-400 font-bold text-lg">+{roi}%</div>
          <div className="text-slate-500 text-xs">ROI</div>
        </div>
      </div>

      {/* Follow button */}
      <button
        onClick={() => setFollowing(!following)}
        className={`w-full py-2.5 rounded-xl font-semibold text-sm transition-all ${
          following
            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/50 hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/50'
            : 'bg-emerald-500 hover:bg-emerald-400 text-white'
        }`}
      >
        {following ? 'Siguiendo ✓' : 'Seguir'}
      </button>
    </div>
  )
}
