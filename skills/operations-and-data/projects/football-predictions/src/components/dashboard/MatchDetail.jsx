import { MOCK_EVENTS, MOCK_TIPSTERS } from '../../api/polymarket'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

const FORM_COLOR = { W: 'bg-emerald-500', D: 'bg-slate-500', L: 'bg-red-500' }

function generatePriceHistory(base) {
  const now = Date.now()
  return Array.from({ length: 7 }, (_, i) => ({
    day: ['L', 'M', 'X', 'J', 'V', 'S', 'D'][i],
    home: Math.max(20, Math.min(80, base + (Math.random() - 0.5) * 10)),
    draw: Math.max(10, Math.min(40, 27 + (Math.random() - 0.5) * 6)),
  }))
}

const H2H = [
  { label: 'Últimos 5 enfrentamientos', home: 2, draw: 1, away: 2 },
  { label: 'Temporada actual', home: 1, draw: 0, away: 0 },
]

export default function MatchDetail({ matchId, onClose }) {
  const match = MOCK_EVENTS.find((m) => m.id === matchId) || MOCK_EVENTS[0]
  const { teams, probabilities, date, league } = match

  const priceHistory = generatePriceHistory(probabilities.home)
  const pieData = [
    { name: 'Local', value: probabilities.home, color: '#10b981' },
    { name: 'Empate', value: probabilities.draw, color: '#64748b' },
    { name: 'Visitante', value: probabilities.away, color: '#f87171' },
  ]

  const homeForm = ['W', 'W', 'D', 'W', 'L']
  const awayForm = ['L', 'W', 'W', 'D', 'W']

  return (
    <div
      className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-start justify-center overflow-y-auto py-8 px-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-3xl bg-[#0F172A] rounded-2xl border border-white/10 shadow-2xl">
        {/* Header */}
        <div className="relative bg-[#1E293B] rounded-t-2xl p-6 border-b border-white/5">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-slate-400 hover:text-white text-2xl leading-none"
          >
            ×
          </button>
          <div className="text-xs text-slate-500 mb-3 uppercase tracking-wider">
            {league === 'laliga' ? 'La Liga' : 'Segunda División'} —{' '}
            {new Date(date).toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}
          </div>
          <div className="flex items-center justify-center gap-8">
            <div className="text-center">
              <div className="text-4xl mb-2">{teams.home.badge}</div>
              <div className="text-white font-bold text-lg">{teams.home.name}</div>
            </div>
            <div className="text-slate-500 font-bold text-2xl">VS</div>
            <div className="text-center">
              <div className="text-4xl mb-2">{teams.away.badge}</div>
              <div className="text-white font-bold text-lg">{teams.away.name}</div>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Probability Panel */}
          <div>
            <h3 className="text-white font-bold mb-4">Probabilidades del Mercado</h3>
            <div className="grid grid-cols-2 gap-4">
              {/* Pie chart */}
              <div className="bg-[#1E293B] rounded-2xl p-4">
                <ResponsiveContainer width="100%" height={180}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={75}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {pieData.map((entry) => (
                        <Cell key={entry.name} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(v) => [`${v}%`, '']}
                      contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: '8px', color: '#fff' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              {/* Legend */}
              <div className="bg-[#1E293B] rounded-2xl p-4 flex flex-col justify-center space-y-3">
                {pieData.map((d) => (
                  <div key={d.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ background: d.color }} />
                      <span className="text-slate-400 text-sm">{d.name}</span>
                    </div>
                    <span className="text-white font-bold text-sm">{d.value}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Price History Chart */}
          <div>
            <h3 className="text-white font-bold mb-4">Evolución de Probabilidades (7 días)</h3>
            <div className="bg-[#1E293B] rounded-2xl p-4">
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={priceHistory}>
                  <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                  <Tooltip
                    formatter={(v, name) => [`${v.toFixed(1)}%`, name === 'home' ? teams.home.name : 'Empate']}
                    contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: '8px', color: '#fff' }}
                  />
                  <Line type="monotone" dataKey="home" stroke="#10b981" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="draw" stroke="#64748b" strokeWidth={2} dot={false} strokeDasharray="4 2" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* H2H + Form */}
          <div className="grid grid-cols-2 gap-4">
            {/* H2H */}
            <div className="bg-[#1E293B] rounded-2xl p-4">
              <h3 className="text-white font-bold mb-3 text-sm">Historial H2H</h3>
              {H2H.map((row) => (
                <div key={row.label} className="mb-3">
                  <div className="text-slate-500 text-xs mb-1">{row.label}</div>
                  <div className="flex gap-1 h-2 rounded-full overflow-hidden">
                    <div className="bg-emerald-500" style={{ width: `${(row.home / 3) * 100}%` }} />
                    <div className="bg-slate-500" style={{ width: `${(row.draw / 3) * 100}%` }} />
                    <div className="bg-red-400" style={{ width: `${(row.away / 3) * 100}%` }} />
                  </div>
                  <div className="flex justify-between text-xs text-slate-400 mt-1">
                    <span className="text-emerald-400">{row.home}V</span>
                    <span>{row.draw}E</span>
                    <span className="text-red-400">{row.away}D</span>
                  </div>
                </div>
              ))}
            </div>
            {/* Form */}
            <div className="bg-[#1E293B] rounded-2xl p-4">
              <h3 className="text-white font-bold mb-3 text-sm">Forma Reciente</h3>
              <div className="mb-3">
                <div className="text-slate-500 text-xs mb-2">{teams.home.name}</div>
                <div className="flex gap-1">
                  {homeForm.map((r, i) => (
                    <span key={i} className={`w-7 h-7 rounded-lg ${FORM_COLOR[r]} text-white text-xs font-bold flex items-center justify-center`}>
                      {r}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-slate-500 text-xs mb-2">{teams.away.name}</div>
                <div className="flex gap-1">
                  {awayForm.map((r, i) => (
                    <span key={i} className={`w-7 h-7 rounded-lg ${FORM_COLOR[r]} text-white text-xs font-bold flex items-center justify-center`}>
                      {r}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Community Consensus */}
          <div className="bg-[#1E293B] rounded-2xl p-4">
            <h3 className="text-white font-bold mb-3">Consenso de la Comunidad</h3>
            <div className="space-y-2">
              {[
                { label: teams.home.name, pct: probabilities.home, color: 'bg-emerald-500' },
                { label: 'Empate', pct: probabilities.draw, color: 'bg-slate-500' },
                { label: teams.away.name, pct: probabilities.away, color: 'bg-red-400' },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-3">
                  <div className="w-24 text-slate-400 text-sm text-right">{item.label}</div>
                  <div className="flex-1 bg-slate-800 rounded-full h-3">
                    <div
                      className={`${item.color} h-3 rounded-full transition-all`}
                      style={{ width: `${item.pct}%` }}
                    />
                  </div>
                  <div className="w-10 text-white text-sm font-semibold">{item.pct}%</div>
                </div>
              ))}
            </div>
          </div>

          {/* Tipster Opinions */}
          <div>
            <h3 className="text-white font-bold mb-4">Opinión de los Tipsters</h3>
            <div className="space-y-3">
              {MOCK_TIPSTERS.slice(0, 3).map((tipster) => {
                const pick = ['Local', 'Empate', 'Visitante'][Math.floor(Math.random() * 3)]
                return (
                  <div key={tipster.id} className="bg-[#1E293B] rounded-xl p-4 flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-sm flex-shrink-0">
                      {tipster.avatar}
                    </div>
                    <div className="flex-1">
                      <div className="text-white font-semibold text-sm">{tipster.name}</div>
                      <div className="text-slate-500 text-xs">{tipster.specialty} · {tipster.hitRate}% hit rate</div>
                    </div>
                    <div className="text-right">
                      <div className="text-amber-400 font-bold text-sm">{pick}</div>
                      <div className="text-slate-500 text-xs">pronóstico</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
